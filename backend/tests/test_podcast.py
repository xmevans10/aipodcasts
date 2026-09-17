import unittest
from podcast import validate_podcast, narration_script

class PodcastTests(unittest.TestCase):
    def setUp(self):
        self.source = {'title': 'Growth across a leaf', 'attribution': 'Kate Harline, Brendan Lane'}
        self.draft = {'title': 'The quiet achievement', 'caveat': 'The sample was small.',
                      'body': 'How does a leaf stay flat? Today: The quiet achievement. Kate Harline and colleagues explore this in Growth across a leaf. The sample was small. Look again at that leaf.'}
    def test_spoken_citation(self): validate_podcast(self.draft, self.source)
    def test_missing_author_is_rejected(self):
        self.draft['body'] = self.draft['body'].replace('Kate Harline', 'A scientist')
        with self.assertRaisesRegex(ValueError, 'author'): validate_podcast(self.draft, self.source)
    def test_missing_paper_is_rejected(self):
        self.draft['body'] = self.draft['body'].replace('Growth across a leaf', 'some new research')
        with self.assertRaisesRegex(ValueError, 'paper title'): validate_podcast(self.draft, self.source)
    def test_unspoken_limitation_is_rejected(self):
        self.draft['body'] = self.draft['body'].replace('The sample was small.', '')
        with self.assertRaisesRegex(ValueError, 'limitations'): validate_podcast(self.draft, self.source)
    def test_audio_does_not_repeat_headline_or_caveat(self):
        script = narration_script(self.draft)
        self.assertEqual(script.count(self.draft['title']), 1)
        self.assertEqual(script.count(self.draft['caveat']), 1)
        self.assertIn('full author credits', script)

if __name__ == '__main__': unittest.main()
