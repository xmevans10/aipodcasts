"""Read-only beta feed server. Bind to loopback; put a TLS reverse proxy in front."""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from pipeline import DATA, connect, feed
from hosts import HOSTS
from pages import render_episode, render_show

ICON = Path(__file__).resolve().parent.parent / 'ios' / 'Zwicky' / 'Assets.xcassets' / 'AppIcon.appiconset' / 'AppIcon.png'


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self): self.serve(head=True)
    def do_GET(self): self.serve()
    def serve(self, head=False):
        path = urlparse(self.path).path
        if path == '/health':
            return self.respond(200, b'{"status":"ok"}', head=head)
        db = connect()
        try:
            if path == '/v1/stories':
                body = json.dumps(feed(db, os.environ.get('LILT_PUBLIC_ORIGIN', 'https://localhost'))).encode()
                return self.respond(200, body, head=head)
            if path == '/icon.png':
                if not ICON.is_file(): return self.respond(404, b'{"error":"not_found"}', head=head)
                return self.respond_bytes(ICON.read_bytes(), 'image/png', head=head)
            if path == '/.well-known/apple-app-site-association':
                team = os.environ.get('LILT_APP_TEAM', '8K5ZVPCQ42')
                bundle = os.environ.get('LILT_APP_BUNDLE', 'com.xmevans10.Zwicky')
                aasa = {"applinks": {"details": [{"appIDs": [team + '.' + bundle],
                        "components": [{"/": "/e/*"}, {"/": "/s/*"}]}]}}
                return self.respond(200, json.dumps(aasa).encode(), head=head)
            origin = os.environ.get('LILT_PUBLIC_ORIGIN', 'https://localhost')
            episode = re.fullmatch(r'/e/([a-f0-9]{20})', path)
            if episode:
                entry = next((e for e in feed(db, origin) if e['id'] == episode.group(1)), None)
                if entry is None: return self.respond(404, b'{"error":"not_found"}', head=head)
                return self.respond_html(render_episode(entry, origin), head=head)
            show = re.fullmatch(r'/s/([a-z0-9-]+)', path)
            if show:
                host_id = show.group(1)
                if host_id not in HOSTS: return self.respond(404, b'{"error":"not_found"}', head=head)
                entries = [e for e in feed(db, origin) if e['hostID'] == host_id or host_id in (e.get('hostIDs') or [])]
                return self.respond_html(render_show(host_id, entries, origin), head=head)
            match = re.fullmatch(r'/audio/([a-f0-9]{20}\.mp3)', path)
            if match:
                filename = match.group(1)
                if not db.execute("SELECT 1 FROM stories WHERE state='published' AND audio=?", (filename,)).fetchone():
                    return self.respond(404, b'{"error":"not_found"}', head=head)
                file = DATA / 'audio' / filename
                if not file.is_file(): return self.respond(404, b'{"error":"not_found"}', head=head)
                size = file.stat().st_size
                start, end, status = 0, size - 1, 200
                raw_range = self.headers.get('Range')
                if raw_range:
                    m = re.fullmatch(r'bytes=(\d*)-(\d*)', raw_range)
                    if not m or (not m[1] and not m[2]): return self.range_error(size)
                    if not m[1]: start = max(0, size - int(m[2]))
                    else:
                        start = int(m[1]); end = min(size - 1, int(m[2])) if m[2] else size - 1
                    if start > end or start >= size: return self.range_error(size)
                    status = 206
                self.send_response(status)
                self.send_header('Content-Type', 'audio/mpeg')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Length', str(end - start + 1))
                self.send_header('Cache-Control', 'no-store')
                if status == 206: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                self.end_headers()
                if not head:
                    with file.open('rb') as f:
                        f.seek(start); remaining = end - start + 1
                        while remaining:
                            block = f.read(min(65536, remaining))
                            if not block: break
                            self.wfile.write(block); remaining -= len(block)
                return
            return self.respond(404, b'{"error":"not_found"}', head=head)
        finally: db.close()
    def range_error(self, size):
        self.send_response(416); self.send_header('Content-Range', f'bytes */{size}'); self.send_header('Content-Length', '0'); self.end_headers()
    def respond(self, status, body, head=False):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head: self.wfile.write(body)
    def respond_bytes(self, body, content_type, head=False):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head: self.wfile.write(body)
    def respond_html(self, html, head=False):
        self.respond_bytes(html.encode(), 'text/html; charset=utf-8', head=head)
    def log_message(self, *args): pass  # Deliberately avoid request/IP logs in beta.

if __name__ == '__main__':
    origin = os.environ.get('LILT_PUBLIC_ORIGIN', '')
    if not origin.startswith('https://'):
        raise SystemExit('Set LILT_PUBLIC_ORIGIN to the HTTPS public origin before serving.')
    ThreadingHTTPServer((os.environ.get('LILT_BIND', '127.0.0.1'), int(os.environ.get('PORT', '8787'))), Handler).serve_forever()
