"""Release provenance shared by narration, publishing and catalog migration."""
from __future__ import annotations

import hashlib
import json

SELECTION = 'major-source-first-v2'
WRITING = 'avoid-ai-writing-v3.38.0'
REVIEW = 'audience-review-v6'


def coverage_for(doi, rows):
    from autoselect import FEEDS
    from major_sources import trusted_url
    if not isinstance(doi, str) or not doi or not isinstance(rows, list) or not rows:
        raise ValueError('Missing traceable major-source coverage')
    for row in rows:
        if (not isinstance(row, dict) or row.get('doi', '').casefold() != doi.casefold()
                or row.get('source') not in FEEDS or row.get('match') != 'explicit_doi'
                or not trusted_url(row.get('url', ''), FEEDS[row['source']][0])):
            raise ValueError('Invalid or mismatched major-source coverage')
    return rows


def require_transcript(artifact):
    if artifact.get('selection_policy') != SELECTION:
        raise ValueError('Transcript predates the required editorial selection policy')
    from show_routing import VERSION
    routing = artifact.get('routing') or {}
    if (routing.get('version') != VERSION or routing.get('host') != artifact.get('host')
            or routing.get('doi') != artifact.get('doi')):
        raise ValueError('Transcript lacks matching source-only show routing')
    return coverage_for(artifact.get('doi'), artifact.get('major_sources'))


def script_hash(story):
    fields = {key: story.get(key) for key in ('title', 'dek', 'body', 'caveat', 'hostID', 'sources')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def stamp(story, artifact):
    return {'selection': SELECTION, 'writing': WRITING, 'review': REVIEW,
            'doi': artifact['doi'], 'coverage': require_transcript(artifact),
            'routing': artifact['routing'],
            'scriptSHA256': script_hash(story)}


def require_story(story):
    policy = story.get('editorialPolicy') or {}
    if any(policy.get(k) != v for k, v in (
            ('selection', SELECTION), ('writing', WRITING), ('review', REVIEW))):
        raise ValueError('Episode does not use the current editorial policy')
    require_transcript({'selection_policy': policy.get('selection'), 'doi': policy.get('doi'),
                        'major_sources': policy.get('coverage'), 'host': story.get('hostID'),
                        'routing': policy.get('routing')})
    if policy.get('scriptSHA256') != script_hash(story):
        raise ValueError('Editorial provenance is stale for this script')
