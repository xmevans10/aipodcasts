import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hosts import HOSTS, writing_guide
from podcast import PODCAST_INSTRUCTIONS, validate_podcast


class HostPersonalityTests(unittest.TestCase):
    def test_every_host_is_distinct_and_complete(self):
        self.assertEqual(set(HOSTS), {
            'nova', 'fern', 'ada', 'atlas', 'ines', 'dev',
            'spinner', 'yusuf', 'noor', 'marek', 'tomas', 'lena',
            'rosa', 'amara', 'kenji', 'freya',
            'jax', 'kai', 'benny', 'chase',
        })
        for key, host in HOSTS.items():
            self.assertEqual(key, host.id)
            self.assertTrue(host.analogies_from and host.avoid and host.emotion_palette)
            self.assertTrue(host.sign_off.startswith("I'm "))
        # Names and sign-offs are per-presenter. Show and topic are intentionally
        # shared by the two hosts of a dialogue show.
        for attribute in ('name', 'sign_off'):
            values = [getattr(h, attribute) for h in HOSTS.values()]
            self.assertEqual(len(set(values)), len(values), attribute)

    def test_guide_carries_the_personality_into_the_prompt(self):
        guide = writing_guide('ada')
        host = HOSTS['ada']
        for fragment in (host.name, host.show, host.persona, host.delivery, host.sign_off, host.avoid[0]):
            self.assertIn(fragment, guide)
        self.assertIn('never let it alter a finding', guide.lower())
        self.assertNotIn(HOSTS['nova'].name, guide)

    def test_instructions_stay_shared_across_hosts(self):
        for host_id in HOSTS:
            self.assertTrue((PODCAST_INSTRUCTIONS + writing_guide(host_id)).startswith(PODCAST_INSTRUCTIONS))

    def test_voice_env_matches_host_id(self):
        self.assertEqual(HOSTS['fern'].voice_env, 'ELEVENLABS_VOICE_FERN')

    def test_sign_off_is_required_in_the_closing(self):
        source = {'title': 'A paper', 'attribution': 'Ada Lovelace, others'}
        # The paper title is spoken once: repeating it now fails spoken_defects.
        body = ('A clearer picture. A paper by Ada Lovelace and colleagues. '
                + ('They followed the same question for years. ' * 5)
                + 'Limitations apply here. ' + HOSTS['ada'].sign_off)
        draft = {'title': 'A clearer picture', 'dek': 'd', 'body': body, 'caveat': 'Limitations apply here.', 'claims': []}
        validate_podcast(draft, source, HOSTS['ada'])
        draft['body'] = body.replace(HOSTS['ada'].sign_off, "That's all for today.")
        with self.assertRaises(ValueError):
            validate_podcast(draft, source, HOSTS['ada'])
        validate_podcast(draft, source)  # host optional: unchanged behaviour without a profile


if __name__ == '__main__':
    unittest.main()
