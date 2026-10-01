import copy
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from withdraw_episode import plan, apply, encode
from publish_feed import episode_page, merge_feed

BASE = 'https://cdn.example'


def episode(name='abc'):
    return {'id': 'episode-' + name, 'title': 'A finding', 'body': 'Original spoken science.',
            'hostID': 'nova', 'published': '2026-10-01', 'minutes': 3,
            'audioURL': f'{BASE}/v1/audio/{name}.m4a',
            'detailURL': f'{BASE}/v1/episodes/{name}.json',
            'shareURL': f'{BASE}/v1/listen/episode-{name}.html',
            'sources': [{'url': 'https://doi.org/10.1234/example'}]}


class WithdrawalTests(unittest.TestCase):
    def test_saved_identity_retained_and_no_audio_or_old_transcript_on_notice(self):
        feed = [episode()]
        result = plan(feed, 'episode-abc', 'A material finding needs correction <script>.')
        tombstone = result['feed'][0]
        self.assertEqual(tombstone['id'], 'episode-abc')
        self.assertIsNone(tombstone['audioURL'])
        self.assertNotIn('Original spoken science', tombstone['body'])
        self.assertEqual(feed[0]['body'], 'Original spoken science.')
        page = episode_page(tombstone).decode()
        self.assertNotIn('<audio', page)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_unknown_and_unplayable_replacement_rejected(self):
        with self.assertRaises(ValueError):
            plan([episode()], 'episode-abc', 'A finding needs correction.', 'missing')
        with self.assertRaises(ValueError):
            plan([episode()], 'episode-abc', 'Too short')

    def test_conditional_feed_write_precedes_asset_changes_and_deletion(self):
        reviewed = plan([episode()], 'episode-abc', 'A material finding needs correction.')
        client = Mock()
        client.get_object.return_value = {'Body': io.BytesIO(encode([episode()])), 'ETag': 'etag'}
        apply(client, 'bucket', 'v1', BASE, reviewed)
        calls = client.mock_calls
        feed_write = next(i for i,c in enumerate(calls) if c[0] == 'put_object' and c.kwargs['Key'] == 'v1/feed.json')
        self.assertEqual(calls[feed_write].kwargs['IfMatch'], 'etag')
        public_writes = [i for i,c in enumerate(calls) if c[0] == 'put_object' and '/.release/' not in c.kwargs['Key']]
        self.assertEqual(min(public_writes), feed_write)
        self.assertGreater(next(i for i,c in enumerate(calls) if c[0] == 'delete_object'), feed_write)

    def test_changed_feed_or_cas_failure_never_mutates_public_assets(self):
        reviewed = plan([episode()], 'episode-abc', 'A material finding needs correction.')
        client = Mock()
        client.get_object.return_value = {'Body': io.BytesIO(encode([episode('changed')])), 'ETag': 'new'}
        with self.assertRaisesRegex(ValueError, 'Feed changed'):
            apply(client, 'bucket', 'v1', BASE, reviewed)
        client.put_object.assert_not_called(); client.delete_object.assert_not_called()
        client.reset_mock()
        client.get_object.return_value = {'Body': io.BytesIO(encode([episode()])), 'ETag': 'etag'}
        def put(**kwargs):
            if kwargs['Key'] == 'v1/feed.json': raise RuntimeError('412 PreconditionFailed')
        client.put_object.side_effect = put
        with self.assertRaises(RuntimeError):
            apply(client, 'bucket', 'v1', BASE, reviewed)
        client.delete_object.assert_not_called()
        self.assertFalse(any(c.kwargs['Key'].startswith('v1/episodes/') for c in client.put_object.call_args_list))

    def test_corrected_edition_keeps_old_withdrawal_and_daily_slots(self):
        old = plan([episode()], 'episode-abc', 'A material finding needs correction.')['feed'][0]
        revised = episode('replacement')
        merged = merge_feed([old], [revised], day='2026-10-01', max_per_day=1)
        self.assertEqual({s['id'] for s in merged}, {'episode-abc', 'episode-replacement'})
        linked = plan(merged, 'episode-abc', 'A material finding needs correction.', 'episode-replacement')
        self.assertEqual(next(s for s in linked['feed'] if s['id']=='episode-abc')['replacementID'], 'episode-replacement')
