import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smc import (expert_reactions, is_expert_reaction, parse_feed, reactions_for_host)

FEED = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title><![CDATA[Expert reaction to study on REM sleep and disease risk]]></title>
    <link>https://www.sciencemediacentre.org/expert-reaction-to-rem-sleep/</link>
    <pubDate>Mon, 21 Sep 2026 09:00:00 +0000</pubDate>
    <category><![CDATA[sleep]]></category>
    <category><![CDATA[brain & neuroscience]]></category>
  </item>
  <item>
    <title><![CDATA[Expert reaction to air pollutants and suicide risk]]></title>
    <link>https://www.sciencemediacentre.org/expert-reaction-to-air-pollutants/</link>
    <pubDate>Sun, 20 Sep 2026 09:00:00 +0000</pubDate>
    <category><![CDATA[mental health]]></category>
  </item>
  <item>
    <title><![CDATA[The state of global water resources 2025]]></title>
    <link>https://www.sciencemediacentre.org/water/</link>
    <pubDate>Sat, 19 Sep 2026 09:00:00 +0000</pubDate>
    <category><![CDATA[water]]></category>
  </item>
</channel></rss>"""


def feed_fetch(url):
    return ("text", FEED)


class SmcTests(unittest.TestCase):
    def test_parse_feed(self):
        items = parse_feed(FEED)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["categories"], ["sleep", "brain & neuroscience"])
        self.assertIn("expert-reaction-to-rem-sleep", items[0]["url"])

    def test_expert_reactions_filtered(self):
        reactions = expert_reactions(feed_fetch)
        self.assertEqual(len(reactions), 2)
        self.assertTrue(all(is_expert_reaction(r["title"]) for r in reactions))

    def test_reactions_for_sleep_host(self):
        reactions = expert_reactions(feed_fetch)
        matched = reactions_for_host("lena", reactions)
        self.assertEqual(len(matched), 1)
        self.assertIn("REM sleep", matched[0]["title"])

    def test_reactions_for_brain_host(self):
        reactions = expert_reactions(feed_fetch)
        matched = reactions_for_host("ada", reactions)
        titles = [r["title"] for r in matched]
        self.assertTrue(any("sleep" in t for t in titles))
        self.assertTrue(any("pollutants" in t for t in titles))

    def test_unmapped_host_gets_no_caveats(self):
        self.assertEqual(reactions_for_host("spinner", expert_reactions(feed_fetch)), [])

    def test_limit_caps_matches(self):
        reactions = expert_reactions(feed_fetch)
        self.assertLessEqual(len(reactions_for_host("ada", reactions, limit=1)), 1)

    def test_bad_xml_is_ignored(self):
        self.assertEqual(parse_feed("<not-xml"), [])
        self.assertEqual(expert_reactions(lambda url: ("text", "<not-xml")), [])

    def test_feed_failure_returns_empty(self):
        self.assertEqual(expert_reactions(lambda url: ("error", "network")), [])


if __name__ == "__main__":
    unittest.main()
