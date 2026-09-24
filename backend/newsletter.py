"""Zwicky newsletter: render an episode (transcript + audio) as a
well-designed email, and stage it for delivery.

No third-party service or dependency. `render` writes a responsive HTML email,
a plain-text alternative and a copy of the episode audio for local preview.
`send` stages one RFC 822 `.eml` per recipient in an outbox (drag into any mail
client), or sends over SMTP only when SMTP_* environment variables are set.

Run from the project root:
    python3 backend/newsletter.py render
    python3 backend/newsletter.py render --episodes clara --open
    python3 backend/newsletter.py send --to reader@example.com
    python3 backend/newsletter.py send --to reader@example.com --attach-audio
"""
from __future__ import annotations
import argparse
import datetime as dt
import email.message
import html
import os
from pathlib import Path
import re
import shutil
import smtplib
import sys
from string import Template
import webbrowser
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from hosts import HOSTS

EPISODES = ROOT / "rendered-episodes"
DEFAULT_OUT = ROOT / "build" / "newsletter"
APP_URL = "https://zwicky.app"
UNSUBSCRIBE_URL = "https://zwicky.app/newsletter/unsubscribe?token={{token}}"

# Show palette mirrors the SwiftUI `Show.all` values in ios/Zwicky/Models.swift.
COLORS = {
    "nova": {"light": "#8F7CFF", "mid": "#4B49C8", "dark": "#151A52"},
    "fern": {"light": "#A8E063", "mid": "#2FA46B", "dark": "#0C3B2E"},
    "ada": {"light": "#FF9A5A", "mid": "#E4572E", "dark": "#5B1A12"},
    "atlas": {"light": "#59D8D0", "mid": "#139BB0", "dark": "#07374A"},
}
CANVAS, INK, SECONDARY, HAIRLINE, SUBTLE = "#FAF9F6", "#161614", "#6B6964", "#E5E2DB", "#F1EFEA"
SERIF = "Charter, 'Iowan Old Style', Georgia, 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(value):
    return html.escape(value or "", quote=True)


def hosted_audio_url(value):
    """Only public HTTPS audio links are safe to put in a staged email."""
    parsed = urlparse(value or "")
    return value if parsed.scheme == "https" and parsed.netloc and not parsed.username else None


def load_episode(episode_id):
    path = EPISODES / (episode_id + ".json")
    if not path.exists():
        raise SystemExit("No rendered episode " + episode_id + " (expected " + str(path) + ")")
    document = __import__("json").loads(path.read_text())
    # Rendered files wrap the feed story (which carries title/body/sources) alongside timings.
    return document.get("story", document)


def available_episodes():
    return sorted(p.stem for p in EPISODES.glob("*.json"))


def show_for(host_id):
    host = HOSTS.get(host_id)
    colors = COLORS.get(host_id, COLORS["fern"])
    return {
        "show": host.show if host else host_id.title(),
        "host": host.name if host else host_id,
        "topic": host.topic if host else "",
        "colors": colors,
    }


def paragraphs(body):
    return [p.strip() for p in re.split(r"\n\s*\n", (body or "").strip()) if p.strip()]


def reading_minutes(story):
    words = len((story.get("body") or "").split())
    return max(1, round(words / 150))


def _button(label, url, color, *, bg=None, fg="#FFFFFF"):
    bg = bg or color
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">'
        '<tr><td align="center" bgcolor="' + bg + '" style="border-radius:10px;">'
        '<a href="' + esc(url) + '" target="_blank" style="display:inline-block;padding:15px 30px;'
        'font-family:' + SANS + ';font-size:16px;font-weight:700;letter-spacing:.2px;color:' + fg + ';'
        'text-decoration:none;border-radius:10px;">' + esc(label) + "</a>"
        "</td></tr></table>"
    )


def render_html(story, info, *, audio_url, recipient_name=None, token="preview"):
    c = info["colors"]
    greeting = ("Hi " + esc(recipient_name) + ", ") if recipient_name else ""
    subject_minutes = reading_minutes(story)
    paras = paragraphs(story.get("body"))
    transcript = "\n".join(
        '<p style="margin:0 0 18px;font-family:' + SERIF + ';font-size:18px;line-height:1.7;color:' + INK + ';">' + esc(p) + "</p>"
        for p in paras
    )
    sources = "".join(
        '<p style="margin:0 0 10px;font-family:' + SANS + ';font-size:13px;line-height:1.6;color:' + SECONDARY + ';">'
        '<a href="' + esc(s.get("url", "")) + '" target="_blank" style="color:' + c["mid"] + ';text-decoration:underline;">'
        + esc(" ".join(s.get("title", "").split())) + "</a><br>"
        + esc(s.get("attribution", "")) + " · " + esc(s.get("license", "")) + "</p>"
        for s in story.get("sources", [])
    )
    audio_block = (
        '<p style="margin:16px 0 0;font-family:' + SANS + ';font-size:13px;color:' + SECONDARY + ';">'
        'The button opens the hosted audio in your browser.</p>'
    ) if audio_url else ""
    listen_button = _button("Listen to this episode", audio_url, c["mid"]) if audio_url else ""
    app_cta = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="background:' + SUBTLE + ';border:1px solid ' + HAIRLINE + ';border-radius:14px;">'
        '<tr><td style="padding:26px 26px 28px;">'
        '<p style="margin:0 0 6px;font-family:' + SANS + ';font-size:11px;letter-spacing:1.4px;'
        'text-transform:uppercase;color:' + c["mid"] + ';font-weight:700;">Keep listening</p>'
        '<h2 style="margin:0 0 8px;font-family:' + SERIF + ';font-size:24px;line-height:1.25;color:' + INK + ';">'
        'More stories from Zwicky</h2>'
        '<p style="margin:0 0 18px;font-family:' + SANS + ';font-size:15px;line-height:1.6;color:' + SECONDARY + ';">'
        'Explore the shows and find your next episode.</p>'
        + _button("Explore Zwicky", APP_URL, c["mid"]) +
        "</td></tr></table>"
    )
    preheader = esc((story.get("dek") or "")[:140])
    year = dt.datetime.now().year

    return Template((HERE / "templates" / "newsletter.html").read_text()).substitute(
        canvas=CANVAS, hairline=HAIRLINE, ink=INK, sans=SANS, secondary=SECONDARY,
        serif=SERIF, subtle=SUBTLE, app_cta=app_cta, audio_block=audio_block,
        color_dark=c["dark"], color_light=c["light"], color_mid=c["mid"],
        app_url=esc(APP_URL), host=esc(info["host"]), show=esc(info["show"]),
        topic=esc(info["topic"]), caveat=esc(story.get("caveat")),
        dek=esc(story.get("dek")), title=esc(story.get("title")),
        greeting=greeting, listen_button=listen_button, preheader=preheader,
        sources=sources, subject_minutes=subject_minutes, transcript=transcript,
        year=year, unsubscribe_url=esc(UNSUBSCRIBE_URL.replace("{{token}}", token)),
    )


def render_text(story, info, *, audio_url, recipient_name=None, token="preview"):
    greeting = ("Hi " + recipient_name + ",\n\n") if recipient_name else ""
    lines = [
        "ZWICKY — " + info["show"],
        story.get("title", ""),
        "with " + info["host"] + " · " + str(reading_minutes(story)) + " min listen",
        "",
        story.get("dek", ""),
        "",
        ("LISTEN: " + audio_url) if audio_url else "",
        "",
        "TRANSCRIPT",
        "",
        "\n\n".join(paragraphs(story.get("body"))),
        "",
        "ABOUT THIS EPISODE",
        story.get("caveat", ""),
        "",
        "READ THE RESEARCH",
    ]
    for s in story.get("sources", []):
        lines.append("- " + " ".join(s.get("title", "").split()))
        lines.append("  " + s.get("url", "") + " · " + s.get("license", ""))
    lines += [
        "",
        "MORE FROM ZWICKY",
        "Explore the shows: " + APP_URL,
        "",
        "You're getting this because you signed up for the Zwicky newsletter.",
        "Unsubscribe: " + UNSUBSCRIBE_URL.replace("{{token}}", token),
    ]
    return "\n".join(lines)


def render_episode(episode_id, out_dir, *, audio_url=None, recipient_name=None, token="preview", copy_audio=True):
    story = load_episode(episode_id)
    info = show_for(story.get("hostID", "fern"))
    if audio_url is None:
        audio_url = hosted_audio_url(story.get("audioURL"))
    if audio_url is None and copy_audio:
        audio_name = (story.get("audioURL") or "").replace("bundle:", "")
        if audio_name and (EPISODES / audio_name).exists():
            (out_dir / "audio").mkdir(parents=True, exist_ok=True)
            shutil.copy2(EPISODES / audio_name, out_dir / "audio" / audio_name)
        audio_url = ("audio/" + audio_name) if audio_name else None
    html_doc = render_html(story, info, audio_url=audio_url, recipient_name=recipient_name, token=token)
    text_doc = render_text(story, info, audio_url=audio_url, recipient_name=recipient_name, token=token)
    return {"id": episode_id, "story": story, "info": info, "html": html_doc, "text": text_doc,
            "subject": story.get("title", "Zwicky") + " · Zwicky"}


def build_message(rendered, *, sender, recipient, reply_to=None, attach_audio=False):
    message = email.message.EmailMessage()
    message["Subject"] = rendered["subject"]
    message["From"] = sender
    message["To"] = recipient
    if reply_to:
        message["Reply-To"] = reply_to
    message["List-Unsubscribe"] = "<" + UNSUBSCRIBE_URL.replace("{{token}}", "unsubscribe") + ">"
    message.set_content(rendered["text"])
    message.add_alternative(rendered["html"], subtype="html")
    if attach_audio:
        audio_name = (rendered["story"].get("audioURL") or "").replace("bundle:", "")
        audio_path = EPISODES / audio_name
        if audio_path.exists():
            message.add_attachment(audio_path.read_bytes(), maintype="audio", subtype="mp4", filename=audio_name)
    return message


def command_render(args):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = args.episodes.split(",") if args.episodes else available_episodes()
    rendered = []
    for episode_id in ids:
        item = render_episode(episode_id.strip(), out_dir, audio_url=args.audio_url)
        (out_dir / (item["id"] + ".html")).write_text(item["html"])
        (out_dir / (item["id"] + ".txt")).write_text(item["text"])
        rendered.append(item)
        print("rendered", item["id"], "->", out_dir / (item["id"] + ".html"))
    index = ["<!doctype html><meta charset='utf-8'><title>Zwicky newsletter previews</title>",
             "<body style='background:#FAF9F6;font-family:-apple-system,Helvetica,Arial,sans-serif;padding:40px;'>",
             "<h1 style=\"font-family:Georgia,serif;color:#161614;\">Newsletter previews</h1>"]
    for item in rendered:
        index.append("<p style='font-size:17px;'><a href='" + item["id"] + ".html' style='color:" + item["info"]["colors"]["mid"] + ";'>"
                     + esc(item["subject"]) + "</a></p>")
    (out_dir / "index.html").write_text("\n".join(index))
    print("index ->", out_dir / "index.html")
    if args.open:
        webbrowser.open((out_dir / "index.html").resolve().as_uri())


def command_send(args):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    outbox = out_dir / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    ids = args.episodes.split(",") if args.episodes else available_episodes()
    recipients = [r.strip() for r in args.to.split(",") if r.strip()]
    if not recipients:
        raise SystemExit("Pass --to with at least one address")
    sender = os.environ.get("NEWSLETTER_FROM", "Zwicky <newsletter@zwicky.app>")
    prepared = []
    for episode_id in ids:
        item = render_episode(episode_id.strip(), out_dir, audio_url=args.audio_url, copy_audio=False)
        public_audio = hosted_audio_url(args.audio_url or item["story"].get("audioURL"))
        if not public_audio:
            raise SystemExit("A public HTTPS audio URL is required for email: set --audio-url or story.audioURL")
        prepared.append(render_episode(episode_id.strip(), out_dir, audio_url=public_audio, copy_audio=False))
    written = 0
    for item in prepared:
        for recipient in recipients:
            message = build_message(item, sender=sender, recipient=recipient, attach_audio=args.attach_audio)
            path = outbox / (item["id"] + "--" + re.sub(r"[^A-Za-z0-9]+", "_", recipient) + ".eml")
            path.write_bytes(bytes(message))
            written += 1
            print("staged", path)
    host = os.environ.get("SMTP_HOST")
    if host and args.deliver:
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=30) as server:
            if os.environ.get("SMTP_TLS", "1") == "1":
                server.starttls()
            user, password = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASSWORD")
            if user and password:
                server.login(user, password)
            for item in prepared:
                for recipient in recipients:
                    server.send_message(build_message(item, sender=sender, recipient=recipient, attach_audio=args.attach_audio))
                    print("sent", item["id"], "to", recipient)
    else:
        print("\n" + str(written) + " message(s) staged in", outbox)
        print("No SMTP_HOST set: open the .eml files directly, or set SMTP_HOST/SMTP_USER/SMTP_PASSWORD and pass --deliver to send.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render", help="write HTML/text previews")
    r.add_argument("--episodes", default=None, help="comma-separated ids (default: all)")
    r.add_argument("--out", default=str(DEFAULT_OUT))
    r.add_argument("--audio-url", default=None, help="public HTTPS audio URL (defaults to the episode's hosted URL)")
    r.add_argument("--open", action="store_true")
    s = sub.add_parser("send", help="stage .eml files (and optionally deliver over SMTP)")
    s.add_argument("--to", required=True, help="comma-separated recipients")
    s.add_argument("--episodes", default=None)
    s.add_argument("--out", default=str(DEFAULT_OUT))
    s.add_argument("--audio-url", default=None, help="absolute audio URL to use instead of the local preview copy")
    s.add_argument("--attach-audio", action="store_true")
    s.add_argument("--deliver", action="store_true", help="send over SMTP when SMTP_HOST is configured")
    args = parser.parse_args()
    (command_render if args.command == "render" else command_send)(args)


if __name__ == "__main__":
    main()
