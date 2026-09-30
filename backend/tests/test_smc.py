import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smc import (expert_reactions, is_expert_reaction, parse_feed, reactions_for_host,
                 reactions_for_source)

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

    def test_topic_match_cannot_attach_another_papers_caveats(self):
        hints = reactions_for_host('lena', expert_reactions(feed_fetch))
        page = '<div class="entry-content">Limited sample. <a href="https://doi.org/10.1234/other">Paper</a></div>'
        self.assertEqual(reactions_for_source({'url': 'https://doi.org/10.1234/target'},
                                             hints, lambda url: ('text', page)), [])

    def test_exact_paper_link_in_article_supplies_commentary(self):
        reaction = {'title': 'Expert reaction to sleep', 'url': 'https://example.org/reaction'}
        page = '<nav>Navigation</nav><div class="entry-content"><p>Only one age group.</p><br/><a href="https://doi.org/10.1234/TARGET">Paper</a></div><footer>Other text</footer>'
        result = reactions_for_source({'url': 'https://doi.org/10.1234/target'},
                                      [reaction], lambda url: ('text', page))
        self.assertEqual(result[0]['source_doi'], '10.1234/target')
        self.assertIn('Only one age group.', result[0]['text'])
        self.assertNotIn('Navigation', result[0]['text'])
        self.assertNotIn('Other text', result[0]['text'])

    def test_related_link_outside_article_is_not_a_paper_match(self):
        page = '<div class="entry-content">A different study.</div><footer><a href="https://doi.org/10.1234/target">Related</a></footer>'
        self.assertEqual(reactions_for_source({'url': 'https://doi.org/10.1234/target'},
                                             [{'url': 'https://example.org/reaction'}],
                                             lambda url: ('text', page)), [])

    def test_unavailable_or_unrecognised_page_has_no_supplementary_gate(self):
        source = {'url': 'https://doi.org/10.1234/target'}
        hints = [{'url': 'https://example.org/reaction'}]
        for response in [('error', 'network'), ('text', '<p>Unknown layout</p>')]:
            self.assertEqual(reactions_for_source(source, hints, lambda url: response), [])


if __name__ == "__main__":
    unittest.main()
