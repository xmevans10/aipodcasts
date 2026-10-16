import json
import os
import unittest
from unittest.mock import patch

from show_routing import route
import editorial_policy


class SourceRoutingTests(unittest.TestCase):
    def test_assignment_uses_source_without_proposed_host_or_draft(self):
        for proposed, assigned, title in [
            ('yusuf', 'jax', 'A third galaxy missing dark matter'),
            ('noor', 'ada', 'Plasticity and language in the anaesthetized human hippocampus')]:
            calls = []
            def fetch(url, **kwargs):
                state = json.loads(kwargs['payload']['input'])
                self.assertEqual(set(state['paper']), {'doi', 'title', 'abstract'})
                self.assertIn('neural network as a tool', state['shows']['noor']['scope'])
                result = {'host': assigned, 'question': 'Source question',
                          'outcome': 'Measured result', 'reason': 'Direct subject fit'}
                return json.dumps({'status': 'completed', 'output': [
                    {'content': [{'type': 'output_text', 'text': json.dumps(result)}]}]})
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'configured'}):
                result = route({'host': proposed, 'doi': '10.1234/x', 'title': title, 'abstract': 'Evidence'},
                               fetch=fetch, reserve=lambda *args: calls.append(args))
            self.assertEqual(result['host'], assigned)
            self.assertEqual(len(calls), 1)

    def test_legacy_and_mismatched_routing_cannot_render(self):
        with self.assertRaisesRegex(ValueError, 'selection policy'):
            editorial_policy.require_transcript({'selection_policy': 'major-source-first-v1'})
        with self.assertRaisesRegex(ValueError, 'routing'):
            editorial_policy.require_transcript({'selection_policy': editorial_policy.SELECTION,
                'host': 'noor', 'doi': '10.1234/x',
                'routing': {'version': 'source-question-routing-v1', 'host': 'ada', 'doi': '10.1234/x'}})

    def test_provider_failure_never_falls_back_to_keyword_guess(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'OPENAI_MODEL': 'configured'}):
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                route({'doi': '10.1234/x'}, fetch=lambda *a, **k: b'{"status":"incomplete"}',
                      reserve=lambda *a: None)
