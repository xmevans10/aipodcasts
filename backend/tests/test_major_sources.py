import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autoselect import select, fit
from beats import BEATS
from major_sources import entries, paper_dois, load_coverage, coverage_priority
from pipeline import connect
from publicity import Release, cluster_releases


class MajorSourceTests(unittest.TestCase):
    def test_rss_and_atom_keep_url_and_explicit_identifier(self):
        rss = '<rss><channel><item><title>Crater</title><link>https://news.test/story</link><guid>https://doi.org/10.1234/crater</guid></item></channel></rss>'
        atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Crater</title><link href="https://news.test/story"/><id>https://doi.org/10.1234/crater</id></entry></feed>'
        for xml in (rss, atom):
            self.assertEqual(entries(xml)[0]['doi'], '10.1234/crater')
            self.assertEqual(entries(xml)[0]['url'], 'https://news.test/story')

    def test_only_explicit_primary_metadata_or_body_links_resolve(self):
        self.assertEqual(paper_dois('<footer><a href="https://doi.org/10.1234/unrelated">Elsewhere</a></footer>'), [])
        self.assertEqual(paper_dois('<article><a href="https://doi.org/10.1234/moon?utm=x">Paper</a></article>'), ['10.1234/moon'])
        self.assertEqual(paper_dois('<meta name="citation_doi" content="10.1234/main"><article><a href="https://doi.org/10.1234/old">Prior work</a></article>'), ['10.1234/main'])

    def test_primary_publisher_links_are_preserved(self):
        page = ('<main><a href="https://iopscience.iop.org/article/10.3847/1538-4357/ae6b8d">Paper</a>'
                '<a href="https://www.nature.com/articles/s41586-026-11242-8">Study</a></main>')
        self.assertEqual(paper_dois(page), ['10.1038/s41586-026-11242-8', '10.3847/1538-4357/ae6b8d'])

    def test_news_metadata_does_not_substitute_for_the_underlying_paper(self):
        page = ('<meta name="citation_doi" content="10.1234/news">'
                '<meta name="citation_article_type" content="News">'
                '<article><a href="https://www.science.org/doi/10.1234/study">Paper</a></article>')
        self.assertEqual(paper_dois(page), ['10.1234/study'])

    def test_news_feed_doi_is_not_used_as_the_study_identifier(self):
        xml = ('<rss><channel><item><title>Moon story</title>'
               '<link>https://news.test/content/article/moon</link>'
               '<guid>https://doi.org/10.1234/news</guid><pubDate>2026-10-15</pubDate>'
               '</item></channel></rss>')
        def get(url):
            return ('text', xml if url.endswith('/feed') else
                    '<main><a href="https://doi.org/10.1234/study">Research</a></main>')
        coverage, _ = load_coverage({'science': ('https://news.test/feed', 1)}, get,
                                    dt.date(2026, 10, 1), dt.date(2026, 10, 16))
        self.assertEqual([c['doi'] for c in coverage], ['10.1234/study'])

    def test_external_feed_link_and_old_coverage_cannot_qualify(self):
        xml = '<rss><channel><item><title>Crater</title><link>https://evil.test/story</link></item><item><title>Old</title><link>https://news.test/old</link><pubDate>2020-01-01</pubDate></item></channel></rss>'
        def get(url):
            self.assertEqual(url, 'https://news.test/feed')
            return 'text', xml
        coverage, failures = load_coverage({'science': ('https://news.test/feed', 1)}, get,
                                          dt.date(2026, 10, 1), dt.date(2026, 10, 16))
        self.assertEqual(coverage, [])
        self.assertEqual(failures, [])

    def test_different_dois_with_identical_headlines_stay_separate(self):
        events = cluster_releases([Release('science', 'The Moon changes', doi='10.1234/a'),
                                   Release('nature', 'The Moon changes', doi='10.1234/b')])
        self.assertEqual(len(events), 2)

    def test_syndication_never_accumulates_independent_votes(self):
        items = [{'source': x, 'weight': .5, 'feed_rank': 1} for x in ['physorg', 'sciencedaily']]
        self.assertEqual(coverage_priority(items, {'science'}), coverage_priority(items[:1], {'science'}))

    def test_narrow_show_needs_literal_subject(self):
        for host, title in [('rosa', 'Decomposition of a matrix'), ('lena', 'Rest energy of particles'),
                            ('spinner', 'Silk scaffolds for cell growth'), ('amara', 'Insect behaviour in beetles')]:
            self.assertEqual(fit({'title': title, 'abstract': ''}, BEATS[host]), 0)

    def test_production_selects_only_linked_in_niche_papers_and_records_coverage(self):
        today = dt.date(2026, 10, 16)
        doi = '10.1234/moon'
        xml = '<rss><channel><item><title>A surprising lunar discovery</title><link>https://news.test/story</link><pubDate>2026-10-15</pubDate></item></channel></rss>'
        paper = {'DOI': doi, 'title': ['A hidden crater on the Moon'],
                 'abstract': 'We measured a new crater on the Moon using orbital images.',
                 'issued': {'date-parts': [[2026, 8, 14]]}, 'container-title': ['Science'],
                 'type': 'journal-article', 'license': [{'URL': 'https://creativecommons.org/licenses/by/4.0/'}]}
        seen = []
        def fetch(url):
            seen.append(url)
            if url == 'https://news.test/feed': return 'text', xml
            if url == 'https://news.test/story':
                return 'text', '<article><a href="https://doi.org/10.1234/moon">The study</a></article>'
            if 'api.crossref.org/works/' in url: return 'json', {'message': paper}
            self.fail('Production must not run broad keyword searches or guess a DOI: ' + url)
        with tempfile.TemporaryDirectory() as tmp, patch('autoselect.FEEDS', {'science': ('https://news.test/feed', 1)}):
            db = connect(Path(tmp) / 'test.sqlite3')
            try:
                result = select(db, today=today, fetch=fetch, source='crossref')
                self.assertEqual([w['doi'] for w in result['selected']], [doi])
                self.assertEqual(result['selected'][0]['major_sources'][0]['url'], 'https://news.test/story')
                self.assertEqual(result['selection_policy'], 'major-source-first-v2')
                # Same headline, wrong literal niche: it cannot fill a show slot.
                paper['title'], paper['abstract'] = ['A new chemical catalyst'], 'We tested metal reactions.'
                self.assertEqual(select(db, today=today, fetch=fetch, source='crossref')['selected'], [])
            finally:
                db.close()

    def test_source_outage_abstains_without_filling_from_uncovered_papers(self):
        with tempfile.TemporaryDirectory() as tmp, patch('autoselect.FEEDS', {'science': ('https://news.test/feed', 1)}):
            db = connect(Path(tmp) / 'test.sqlite3')
            try:
                result = select(db, today=dt.date(2026, 10, 16), fetch=lambda url: ('error', 503))
                self.assertEqual(result['selected'], [])
                self.assertTrue(result['source_failures'])
            finally: db.close()
