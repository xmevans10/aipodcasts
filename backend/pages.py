"""Public, account-free pages for shared links: /e/<id> and /s/<host>.

Rendered from the same published feed as the app and the newsletter, so a shared link
can never drift from the audio. Reuses the newsletter palette and escaping helpers.
The pages are static HTML (no JS required) and carry Open Graph / Twitter metadata so
Messages, Slack and social apps show a rich preview.
"""
from __future__ import annotations
from newsletter import COLORS, CANVAS, INK, SECONDARY, HAIRLINE, SUBTLE, SERIF, SANS
from newsletter import esc, paragraphs, show_for


def _meta(title: str, description: str, canonical: str, image: str, *, kind: str = "article") -> str:
    return "\n".join([
        f'<meta name="description" content="{esc(description)}">',
        f'<link rel="canonical" href="{esc(canonical)}">',
        f'<meta property="og:type" content="{kind}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{esc(canonical)}">',
        f'<meta property="og:image" content="{esc(image)}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])


def _sources(items) -> str:
    if not items:
        return ""
    rows = "\n".join(
        f'<li><a href="{esc(s.get("url",""))}">{esc(" ".join(s.get("title","").split()))}</a>'
        f'<br><span class="muted">{esc(s.get("attribution",""))} · {esc(s.get("license",""))}</span></li>'
        for s in items)
    return f'<h2>Sources</h2><ol class="sources">{rows}</ol>'


def _shell(*, title: str, description: str, canonical: str, image: str, accent: str, body: str, kind: str = "article") -> str:
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{_meta(title, description, canonical, image, kind=kind)}
<style>
  :root {{ --canvas:{CANVAS}; --ink:{INK}; --secondary:{SECONDARY}; --hairline:{HAIRLINE}; --subtle:{SUBTLE}; --accent:{accent}; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--canvas); color:var(--ink); font-family:{SANS}; line-height:1.6; }}
  main {{ max-width:680px; margin:0 auto; padding:40px 22px 80px; }}
  a {{ color:var(--accent); }}
  .brand {{ font-family:{SERIF}; font-weight:700; letter-spacing:.6px; }}
  .eyebrow {{ color:var(--secondary); text-transform:uppercase; letter-spacing:1.4px; font-size:11px; font-weight:700; margin:26px 0 8px; }}
  h1 {{ font-family:{SERIF}; font-size:40px; line-height:1.15; margin:0 0 12px; }}
  h2 {{ font-family:{SERIF}; font-size:22px; margin:34px 0 10px; }}
  .dek {{ font-family:{SERIF}; font-size:20px; color:var(--ink); }}
  .hero {{ height:180px; border-radius:16px; margin:18px 0 4px; background:linear-gradient(135deg,{accent},var(--ink)); }}
  .muted {{ color:var(--secondary); font-size:13px; }}
  .transcript p {{ font-family:{SERIF}; font-size:18px; }}
  .sources li {{ margin-bottom:10px; }}
  audio {{ width:100%; margin:14px 0 6px; }}
  .cta {{ display:inline-block; margin-top:26px; padding:14px 22px; border-radius:12px; background:var(--accent); color:#fff; text-decoration:none; font-weight:700; }}
  footer {{ border-top:1px solid var(--hairline); margin-top:44px; padding-top:16px; }}
</style>
</head><body><main>
  <div class="brand">ZWICKY</div>
  {body}
  <footer><p class="muted">Hosts are fictional presenters; every episode is written and narrated with AI and checked against its sources.</p></footer>
</main></body></html>'''


def render_episode(entry: dict, origin: str) -> str:
    origin = origin.rstrip("/")
    canonical = origin + "/e/" + entry["id"]
    image = origin + "/icon.png"
    info = show_for(entry.get("hostID", "nova"))
    accent = info["colors"]["mid"]
    audio = f'<audio controls preload="none" src="{esc(entry.get("audioURL",""))}"></audio>' if entry.get("audioURL") else ""
    transcript = "\n".join(f"<p>{esc(p)}</p>" for p in paragraphs(entry.get("body", "")))
    body = "\n".join([
        f'<div class="eyebrow">{esc(info["show"])} · {esc(info["topic"])}</div>',
        f"<h1>{esc(entry['title'])}</h1>",
        f'<p class="dek">{esc(entry.get("dek",""))}</p>',
        f'<p class="muted">with {esc(info["host"])} · {entry.get("minutes", 1)} min listen</p>',
        '<div class="hero" role="img" aria-label="Episode artwork"></div>',
        audio,
        f'<h2>Transcript</h2><div class="transcript">{transcript}</div>',
        f'<h2>About this episode</h2><p class="muted">{esc(entry.get("caveat",""))}</p>',
        _sources(entry.get("sources", [])),
        '<a class="cta" href="https://apps.apple.com/app/id6813660087">Listen in the Zwicky app</a>',
    ])
    return _shell(title=entry["title"] + " · Zwicky", description=entry.get("dek", ""),
                  canonical=canonical, image=image, accent=accent, body=body)


def render_show(host_id: str, entries: list[dict], origin: str) -> str:
    origin = origin.rstrip("/")
    info = show_for(host_id)
    canonical = origin + "/s/" + host_id
    image = origin + "/icon.png"
    accent = info["colors"]["mid"]
    items = "\n".join(
        f'<li><a href="{esc(origin)}/e/{esc(e["id"])}">{esc(e["title"])}</a>'
        f'<br><span class="muted">{esc(e.get("dek",""))}</span></li>' for e in entries)
    listing = f'<ol class="sources">{items}</ol>' if entries else '<p class="muted">Episodes are in production.</p>'
    body = "\n".join([
        f'<div class="eyebrow">{esc(info["topic"])}</div>',
        f"<h1>{esc(info['show'])}</h1>",
        f'<p class="dek">with {esc(info["host"])}</p>',
        '<div class="hero" role="img" aria-label="Show artwork"></div>',
        "<h2>Episodes</h2>", listing,
        '<a class="cta" href="https://apps.apple.com/app/id6813660087">Follow in the Zwicky app</a>',
    ])
    return _shell(title=info["show"] + " · Zwicky", description=f"{info['show']} with {info['host']} on Zwicky.",
                  canonical=canonical, image=image, accent=accent, body=body, kind="website")
