import json
from hosts import HOSTS
import os
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as p
import server

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.db = p.connect(self.data / 'test.sqlite3')
        self.source = {'title': 'A source article', 'text': 'This is a measured result with considerable uncertainty. ' * 250,
                       'url': 'https://doi.org/10.1371/journal.pbio.123', 'attribution': 'A. Researcher', 'license': 'CC BY 4.0',
                       'licenseURL': 'https://creativecommons.org/licenses/by/4.0/'}
        self.draft = {'title': 'A little scientific wonder', 'dek': 'An accessible explanation of the result.',
                      'body': 'Today: A little scientific wonder. A source article, by A. Researcher. ' + 'Evidence is interesting and uncertainty matters. ' * 50 + 'This result has considerable uncertainty. ' + HOSTS['nova'].sign_off,
                      'caveat': 'This result has considerable uncertainty.',
                      'claims': [{'claim': 'The result has uncertainty.', 'quote': 'This is a measured result with considerable uncertainty.'}]}
        self.id = 'a' * 20
        self.db.execute('INSERT INTO stories(id,source,host) VALUES(?,?,?)', (self.id, json.dumps(self.source), 'nova')); self.db.commit()
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def staged(self):
        self.db.execute("UPDATE stories SET state='review', draft=?", (json.dumps(self.draft),)); self.db.commit()
    def test_valid_draft(self): p.validate_draft(self.draft, self.source)
    def test_hallucinated_evidence_rejected(self):
        self.draft['claims'][0]['quote'] = 'A fabricated scientific quotation.'
        with self.assertRaises(ValueError): p.validate_draft(self.draft, self.source)
    def test_short_script_rejected(self):
        self.draft['body'] = 'A tiny script.'
        with self.assertRaises(ValueError): p.validate_draft(self.draft, self.source)
    def test_unreviewed_narration_blocked(self):
        with self.assertRaises(ValueError): p.narrate(self.db, self.id)
    def test_unreviewed_publication_blocked(self):
        with self.assertRaises(ValueError): p.publish(self.db, self.id)
    def test_drafts_not_public(self):
        self.staged(); self.assertEqual(p.feed(self.db, 'https://feed.example'), [])
    def test_approval_binds_exact_draft(self):
        self.staged(); p.review(self.db, self.id, 'Editor')
        self.db.execute("UPDATE stories SET draft=?", (json.dumps({**self.draft, 'title': 'Changed title after approval'}),)); self.db.commit()
        with self.assertRaisesRegex(ValueError, 'changed'): p.narrate(self.db, self.id)
    def test_call_cap_applies_to_failures_too(self):
        with patch.dict(os.environ, {'LILT_MAX_PROVIDER_CALLS_PER_DAY': '1'}):
            p.reserve_call(self.db, 'test', self.id)
            with self.assertRaises(ValueError): p.reserve_call(self.db, 'test', self.id)
    def test_unknown_source_rejected_without_network(self):
        with patch.object(p, 'request') as request:
            with self.assertRaises(ValueError): p.ingest(self.db, 'https://127.0.0.1', 'nova')
            request.assert_not_called()
    def test_cc_by_xml(self):
        raw = ('<article><front><article-meta><article-id pub-id-type="doi">10.1371/journal.pbio.123</article-id>'
               '<title-group><article-title>A test source</article-title></title-group>'
               '<permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by/4.0/"/></permissions>'
               '</article-meta></front><body><p>' + self.source['text'] + '</p></body></article>').encode()
        self.assertEqual(p.parse_plos_xml(raw, '10.1371/journal.pbio.123')['license'], 'CC BY 4.0')
        with self.assertRaises(ValueError): p.parse_plos_xml(raw.replace(b'/by/', b'/by-nc/'), '10.1371/journal.pbio.123')
    def test_full_source_and_primary_authors_only(self):
        author = '<contrib-group><contrib contrib-type="author"><name><given-names>Primary</given-names><surname>Author</surname></name></contrib></contrib-group>'
        raw = ('<article><front><article-meta><article-id pub-id-type="doi">10.1371/journal.pbio.123</article-id>'
               '<title-group><article-title>A test source</article-title></title-group>' + author +
               '<permissions><license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by/4.0/"/></permissions>'
               '</article-meta></front><body><p>' + ('Full source material. ' * 3500) + 'Final limitation retained.</p></body>'
               '<sub-article><front-stub>' + author.replace('Primary', 'Reviewer') + '</front-stub></sub-article></article>').encode()
        source = p.parse_plos_xml(raw, '10.1371/journal.pbio.123')
        self.assertEqual(source['attribution'], 'Primary Author')
        self.assertGreater(len(source['text']), 60000)
        self.assertTrue(source['text'].endswith('Final limitation retained.'))
    def test_refresh_cannot_change_reviewed_source(self):
        self.staged()
        doi = '10.1371/journal.pbio.123'
        story_id = p.hashlib.sha256((doi + ':nova').encode()).hexdigest()[:20]
        self.db.execute('UPDATE stories SET id=?', (story_id,)); self.db.commit()
        with patch.object(p, 'request') as req:
            with self.assertRaises(ValueError): p.ingest(self.db, doi, 'nova', refresh=True)
            req.assert_not_called()
    def test_env_loader_does_not_execute_or_overwrite(self):
        env = self.data / '.env'
        env.write_text('OPENAI_MODEL=test-model\nOPENAI_API_KEY="literal$(not-a-command)"\nHOME=/wrong\n')
        with patch.dict(os.environ, {'OPENAI_MODEL': 'existing'}, clear=True):
            p.load_local_env(env)
            self.assertEqual(os.environ['OPENAI_MODEL'], 'existing')
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'literal$(not-a-command)')
            self.assertNotIn('HOME', os.environ)
    def test_luna_request_includes_low_reasoning_and_author_metadata(self):
        response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(self.draft)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'gpt-5.6-luna', 'OPENAI_REASONING_EFFORT': 'low'}):
            with patch.object(p, 'request', return_value=json.dumps(response).encode()) as req:
                p.draft_story(self.db, self.id)
                payload = req.call_args.kwargs['payload']
                self.assertEqual(payload['model'], 'gpt-5.6-luna')
                self.assertEqual(payload['reasoning'], {'effort': 'low'})
                self.assertEqual(json.loads(payload['input'])['source_attribution'], 'A. Researcher')
    def test_dialogue_draft_receives_paper_metadata(self):
        # Regression: the dialogue validator checks the opening for the exact paper title
        # and first author, so draft_story must pass metadata, not just evidence text.
        source = {'title': 'Growth across a leaf', 'attribution': 'Kate Harline, Brendan Lane',
                  'text': 'The sample was small. Growth coordination keeps the leaf flat. ' * 40,
                  'url': 'https://doi.org/10.1/x', 'license': 'CC BY 4.0', 'licenseURL': ''}
        ines, dev = HOSTS['ines'], HOSTS['dev']
        dialogue = {
            'title': 'The quiet achievement',
            'dek': 'A second opinion on how a leaf stays flat.',
            'turns': [
                {'speaker': ines.name, 'text': 'Today: The quiet achievement. Kate Harline and colleagues ask how Growth across a leaf stays flat. ' + 'word ' * 220},
                {'speaker': dev.name, 'text': 'Here is why it matters outside the lab, framed as one clearly marked comparison.'},
                {'speaker': ines.name, 'text': 'The method is careful, and the sample was small. ' + ines.sign_off},
                {'speaker': dev.name, 'text': 'That caveat does not spoil the finding, it sharpens it.'},
                {'speaker': ines.name, 'text': 'Exactly. A small clear result still earns its place.'},
                {'speaker': dev.name, 'text': 'And that is the whole story. ' + dev.sign_off},
            ],
            'caveat': 'The sample was small.',
            'claims': [{'claim': 'Coordination keeps the leaf flat',
                        'quote': 'Growth coordination keeps the leaf flat'}],
        }
        story_id = 'd' * 20
        self.db.execute('INSERT INTO stories(id,source,host) VALUES(?,?,?)',
                        (story_id, json.dumps(source), 'ines'))
        self.db.commit()
        response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(dialogue)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'test-model'}):
            with patch.object(p, 'request', return_value=json.dumps(response).encode()):
                draft = p.draft_story(self.db, story_id)
        self.assertEqual(draft['title'], 'The quiet achievement')
        self.assertEqual(len(draft['turns']), 6)

    def test_missing_authors_block_paid_generation(self):
        self.source['attribution'] = 'Authors listed at source'
        self.db.execute('UPDATE stories SET source=?', (json.dumps(self.source),)); self.db.commit()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}), patch.object(p, 'request') as req:
            with self.assertRaisesRegex(ValueError, 'author'): p.draft_story(self.db, self.id)
            req.assert_not_called()
        self.assertEqual(self.db.execute('SELECT count(*) FROM calls').fetchone()[0], 0)
    def test_paid_calls_mocked_end_to_end(self):
        response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(self.draft)}]}]}
        env = {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'test-model', 'ELEVENLABS_API_KEY': 'test', 'ELEVENLABS_VOICE_NOVA': 'licensed_voice'}
        with patch.dict(os.environ, env), patch.object(p, 'DATA', self.data):
            with patch.object(p, 'request', return_value=json.dumps(response).encode()) as req:
                p.draft_story(self.db, self.id); p.draft_story(self.db, self.id)
                self.assertEqual(req.call_count, 1)
            p.review(self.db, self.id, 'Test Editor')
            with patch.object(p, 'request', return_value=b'ID3' + b'x' * 2000) as req:
                p.narrate(self.db, self.id); p.narrate(self.db, self.id)
                self.assertEqual(req.call_count, 1)
            p.publish(self.db, self.id)
            result = p.feed(self.db, 'https://feed.example')
            self.assertEqual(result[0]['audioURL'], f'https://feed.example/audio/{self.id}.mp3')
            self.assertFalse(result[0]['isDemo'])
            self.assertNotIn('claims', result[0])
    def test_audio_range_and_withdrawal(self):
        self.staged(); p.review(self.db, self.id, 'Editor')
        audio = self.data / 'audio'; audio.mkdir(); (audio / (self.id + '.mp3')).write_bytes(b'0123456789')
        self.db.execute("UPDATE stories SET state='published', audio=?", (self.id + '.mp3',)); self.db.commit()
        factory = lambda: p.connect(self.data / 'test.sqlite3')
        with patch.object(server, 'connect', factory), patch.object(server, 'DATA', self.data):
            http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
            url = f'http://127.0.0.1:{http.server_port}/audio/{self.id}.mp3'
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': 'bytes=2-5'})) as response:
                    self.assertEqual(response.status, 206); self.assertEqual(response.read(), b'2345')
                self.db.execute("UPDATE stories SET state='withdrawn'"); self.db.commit()
                with self.assertRaises(urllib.error.HTTPError) as err: urllib.request.urlopen(url)
                self.assertEqual(err.exception.code, 404)
            finally: http.shutdown(); http.server_close(); thread.join()

    def test_language_clues_reach_the_prompt(self):
        response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(self.draft)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'test-model'}):
            with patch.object(p, 'request', return_value=json.dumps(response).encode()) as req:
                p.draft_story(self.db, self.id)
                instructions = req.call_args.kwargs['payload']['instructions']
                self.assertIn('LANGUAGE CLUES for nova', instructions)

    def test_draft_repair_retries_with_the_failure_quoted(self):
        bad = {**self.draft, 'body': 'A tiny script.'}
        bad_response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(bad)}]}]}
        good_response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(self.draft)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'test-model', 'LILT_DRAFT_ATTEMPTS': '2'}):
            with patch.object(p, 'request', side_effect=[json.dumps(bad_response).encode(), json.dumps(good_response).encode()]) as req:
                draft = p.draft_story(self.db, self.id)
                self.assertEqual(req.call_count, 2)
                self.assertIn('REPAIR', req.call_args.kwargs['payload']['instructions'])
                self.assertEqual(draft['title'], self.draft['title'])
                self.assertEqual(self.db.execute('SELECT count(*) FROM calls').fetchone()[0], 2)

    def test_draft_repair_gives_up_after_attempts(self):
        bad = {**self.draft, 'body': 'A tiny script.'}
        bad_response = {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(bad)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'test-model', 'LILT_DRAFT_ATTEMPTS': '2'}):
            with patch.object(p, 'request', return_value=json.dumps(bad_response).encode()):
                with self.assertRaisesRegex(ValueError, 'failed after 2 attempts'):
                    p.draft_story(self.db, self.id)

if __name__ == '__main__': unittest.main()
