"""Curated science coverage is discovery; the linked paper is evidence.

Keep the headline, outlet, URL and feed position attached to every DOI. No fuzzy
headline-to-paper guess can qualify a story. Feed order is not a readership chart.
"""
from __future__ import annotations

import datetime as dt
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

DOI = re.compile(r'10\.\d{4,9}/[^\s<>"\']+', re.I)


def canonical_doi(value):
    value = urllib.parse.unquote(html.unescape(value or '')).split('?', 1)[0].split('#', 1)[0]
    match = DOI.search(value)
    return match.group().rstrip('.,;').casefold() if match else ''


def trusted_url(url, feed_url):
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or '').removeprefix('www.')
    expected = (urllib.parse.urlsplit(feed_url).hostname or '').removeprefix('www.')
    return parsed.scheme == 'https' and host == expected and not parsed.username and not parsed.password


def entries(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    result = []
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] not in ('item', 'entry'):
            continue
        values, links, identifiers = {}, [], []
        for child in node:
            name = child.tag.rsplit('}', 1)[-1]
            value = ''.join(child.itertext()).strip()
            values[name] = value
            if name == 'link' and child.get('rel', 'alternate') == 'alternate':
                links.append(child.get('href') or value)
            if name in ('doi', 'identifier', 'id', 'guid'):
                identifiers.append(value)
        result.append({'title': values.get('title', ''), 'url': next(iter(links), ''),
                       'date': values.get('pubDate') or values.get('published') or values.get('updated') or values.get('date', ''),
                       'doi': next((d for v in identifiers + links if (d := canonical_doi(v))), '')})
    return result


class PaperLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.primary, self.links = set(), set()
        self.news = False
        self.in_article = 0
        self.article_links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('article', 'main'):
            self.in_article += 1
        if tag == 'meta' and 'news' in attrs.get('content', '').lower() and (attrs.get('name') or '').lower() in ('citation_article_type', 'citation_section', 'dc.type'):
            self.news = True
        if tag == 'meta' and (attrs.get('name') or attrs.get('property') or '').lower() in (
                'citation_doi', 'dc.identifier', 'dc.identifier.doi', 'prism.doi'):
            if doi := canonical_doi(attrs.get('content')):
                self.primary.add(doi)
        if tag == 'a':
            url = urllib.parse.urlsplit(html.unescape(attrs.get('href', '')))
            if url.scheme in ('http', 'https'):
                doi = canonical_doi(url.path)
                if not doi and (url.hostname or '').removeprefix('www.') == 'nature.com':
                    match = re.fullmatch(r'/articles/((?:s\d{5}-|nature)[a-zA-Z0-9-]+)', url.path)
                    doi = '10.1038/' + match[1].casefold() if match else ''
                if doi:
                    self.links.add(doi)
                    if self.in_article:
                        self.article_links.add(doi)

    def handle_endtag(self, tag):
        if tag in ('article', 'main'):
            self.in_article = max(0, self.in_article - 1)


def paper_dois(page, excluded=()):
    parser = PaperLinks()
    parser.feed(page)
    # A publisher's citation metadata identifies its main paper. For news, keep
    # explicit paper links in the article body, excluding navigation/footer links.
    excluded = set(excluded)
    primary = parser.primary - excluded
    return sorted((parser.article_links - parser.primary - excluded) if parser.news or excluded
                  else (primary or parser.article_links))


def load_coverage(feeds, get, since, today, max_items=24):
    coverage, failures = [], []
    for outlet, (feed_url, weight) in feeds.items():
        try:
            kind, payload = get(feed_url)
            if kind != 'text':
                failures.append(outlet + ': feed unavailable')
                continue
            feed_items = entries(payload)
            if not feed_items:
                failures.append(outlet + ': empty or unparsable feed')
                continue
            for position, item in enumerate(feed_items[:max_items], 1):
                if not item['date']:
                    continue
                if item['date']:
                    try:
                        day = dt.datetime.fromisoformat(item['date'].replace('Z', '+00:00')).date()
                    except ValueError:
                        try:
                            day = parsedate_to_datetime(item['date']).date()
                        except (ValueError, TypeError):
                            continue
                    if not since <= day <= today:
                        continue
                url = urllib.parse.urljoin(feed_url, item['url'])
                if not trusted_url(url, feed_url):
                    continue
                # A news article's registered DOI identifies the journalism, not its study.
                news = '/content/article/' in url or '/articles/d41586-' in url
                dois = [item['doi']] if item['doi'] and not news else []
                if not dois:
                    kind, page = get(url)
                    if kind == 'text':
                        dois = paper_dois(page, excluded=[item['doi']] if news and item['doi'] else [])
                for doi in dois:
                    coverage.append({'doi': doi, 'source': outlet, 'title': item['title'],
                                     'url': url, 'date': item['date'], 'feed_rank': position,
                                     'weight': weight, 'match': 'explicit_doi'})
        except Exception as error:
            # Partial source outages are visible; they never authorize uncovered fillers.
            failures.append(outlet + ': ' + type(error).__name__)
    return coverage, failures


def coverage_priority(items, independent):
    # Count each outlet once. Syndicated copies collectively contribute at most one
    # secondary vote; independent editorial coverage comes first.
    votes = {}
    for item in items:
        value = item['weight'] / (60 + item['feed_rank'])
        votes[item['source']] = max(votes.get(item['source'], 0), value)
    return (sum(v for source, v in votes.items() if source in independent),
            max((v for source, v in votes.items() if source not in independent), default=0))
