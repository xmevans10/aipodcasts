"""Deterministic evidence selection: zero model calls, intact source paragraphs."""
import json
import re


def category(section):
    section = section.lower()
    if 'abstract' in section: return 'abstract'
    if any(word in section for word in ('limitation', 'caveat')): return 'limitations'
    if any(word in section for word in ('discussion', 'conclusion')): return 'discussion'
    if any(word in section for word in ('method', 'material', 'experimental')): return 'methods'
    if 'result' in section: return 'results'
    if 'introduction' in section: return 'introduction'
    return 'other'


def extract_passages(root, node_text):
    passages = []
    def visit(node, section):
        if node.tag in ('fig', 'table-wrap', 'supplementary-material', 'ref-list'):
            return
        if node.tag == 'sec':
            title = node_text(node.find('title')) or node.get('sec-type', '')
            section = section + ' / ' + title
        if node.tag == 'p':
            value = node_text(node)
            if value:
                passages.append({'id': f'p{len(passages) + 1}', 'section': section, 'text': value})
            return
        for child in node:
            visit(child, section)
    for abstract in root.findall('./front/article-meta/abstract'):
        visit(abstract, 'Abstract')
    body = root.find('./body')
    if body is not None: visit(body, 'Body')
    return passages


def build_packet(source, max_chars=18000):
    """Cap serialized source input characters, not tokens; do not truncate paragraphs.

    This packet is partial evidence, never a substitute for an editor reading the paper.
    Sample/method and caveat heuristics can miss implicit limitations.
    """
    if not 2000 <= max_chars <= 60000:
        raise ValueError('Evidence budget must be between 2000 and 60000 characters')
    raw = source.get('passages') or [
        {'id': f'p{i+1}', 'section': 'Unclassified', 'text': value}
        for i, value in enumerate(source['text'].split('\n\n')) if value.strip()]
    seen, passages = set(), []
    for p in raw:
        fingerprint = ' '.join(p['text'].split())
        if fingerprint in seen: continue
        seen.add(fingerprint); passages.append(p)
    groups = {name: [] for name in ('abstract', 'limitations', 'results', 'discussion', 'methods', 'other', 'introduction')}
    for p in passages:
        kind = category(p['section'])
        # Prioritize explicit caveats wherever they appear, without rewriting them.
        if kind != 'abstract' and re.search(r'\blimitation\b|\blimitations\b|cannot rule out|remain[s]? unclear|under[- ]?count|small sample', p['text'], re.I):
            kind = 'limitations'
        groups[kind].append(p)
    # Bring paragraphs documenting sample sizes toward the front of Results/Methods.
    for name in ('results', 'methods'):
        groups[name].sort(key=lambda p: not bool(re.search(r'\bn\s*=|sample size|replicate|specimen', p['text'], re.I)))
    packet = {'source_title': source['title'],
              'source_attribution': source.get('attribution', ''),
              'source_journal': source.get('journal', ''),
              'scope': 'Selected source paragraphs only. Omitted sections may contain additional evidence or limitations. Do not claim a complete review.',
              'source_characters': len(source['text']), 'omitted_paragraphs': len(passages), 'passages': []}
    selected = set()
    def add(p, required=False):
        if p['id'] in selected: return True
        candidate = {**packet, 'passages': packet['passages'] + [p], 'omitted_paragraphs': len(passages) - len(selected) - 1}
        if len(json.dumps(candidate, ensure_ascii=False)) > max_chars:
            if required: raise ValueError('Required evidence does not fit; increase budget or curate the packet')
            return False
        packet.update(candidate); selected.add(p['id']); return True
    # Reserve coverage across the paper before filling remaining capacity.
    for name in ('abstract', 'limitations', 'results', 'methods', 'discussion'):
        if groups[name]: add(groups[name][0], required=True)
    # Round-robin prevents a long Results section consuming the entire allowance.
    order = ('abstract', 'limitations', 'discussion', 'results', 'methods', 'other', 'introduction')
    for index in range(max((len(v) for v in groups.values()), default=0)):
        for name in order:
            if index < len(groups[name]): add(groups[name][index])
    if not packet['passages']:
        raise ValueError('No intact source paragraph fits the evidence budget')
    # Render selected paragraphs in original reading order, preserving source labels.
    packet['passages'].sort(key=lambda p: int(p['id'][1:]))
    return packet


def evidence_text(packet):
    return '\n\n'.join(p['text'] for p in packet['passages'])
