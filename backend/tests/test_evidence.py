import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import build_packet, evidence_text

class EvidenceTests(unittest.TestCase):
    def source(self):
        passages = []
        for section in ('Abstract', 'Results', 'Methods', 'Discussion', 'Limitations', 'Introduction'):
            for i in range(8):
                passages.append({'id': f'p{len(passages)+1}', 'section': section,
                                 'text': f'{section} paragraph {i}. ' + ('Complete evidence sentence. ' * 15)})
        return {'title': 'A source title', 'passages': passages, 'text': '\n\n'.join(p['text'] for p in passages)}
    def test_budget_and_coverage(self):
        source = self.source(); packet = build_packet(source, 6000)
        self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False)), 6000)
        self.assertGreater(packet['omitted_paragraphs'], 0)
        sections = {p['section'] for p in packet['passages']}
        self.assertTrue({'Abstract', 'Results', 'Methods', 'Discussion', 'Limitations'} <= sections)
        for p in packet['passages']: self.assertIn(p, source['passages'])
    def test_deterministic_and_no_rewriting(self):
        source = self.source()
        self.assertEqual(build_packet(source, 6000), build_packet(source, 6000))
        for paragraph in evidence_text(build_packet(source, 6000)).split('\n\n'):
            self.assertIn(paragraph, source['text'])
    def test_required_evidence_does_not_fit_fails_closed(self):
        source = self.source(); source['passages'][0]['text'] = 'Long abstract. ' * 1000
        with self.assertRaises(ValueError): build_packet(source, 6000)
    def test_duplicate_paragraphs_removed(self):
        source = self.source(); source['passages'].append({**source['passages'][0], 'id': 'p100'})
        packet = build_packet(source, 6000)
        self.assertEqual(len({p['text'] for p in packet['passages']}), len(packet['passages']))
    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError): build_packet(self.source(), 1)

if __name__ == '__main__': unittest.main()

class LeafRegressionTests(unittest.TestCase):
    def test_curated_leaf_evidence_survives_compression(self):
        root = Path(__file__).resolve().parents[1] / 'evals' / 'leaf'
        source = json.loads((root / 'source.json').read_text())
        checks = json.loads((root / 'checks.json').read_text())
        packet = build_packet(source)
        selected = {p['id'] for p in packet['passages']}
        for check in checks:
            self.assertTrue(selected.intersection(check['evidence_ids']), check['id'])
        self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False)), packet['budget_characters'])
        self.assertLessEqual(packet['budget_characters'], 36000)
