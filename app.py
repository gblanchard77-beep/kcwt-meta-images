#!/usr/bin/env python3
"""
Minimal authenticated image host for KCWT Meta poster (code only — not deployed).

Env:
  KCWT_META_IMAGES_SECRET  — shared secret for upload/delete (name only; set in Railway)
  PORT                     — listen port (Railway sets this; default 8080)
  DATA_DIR                 — where to store files (default /data)

API:
  POST /upload   header X-Auth-Secret: <secret>  body: raw image bytes
                 -> 200 {"url": "/i/<64hex>.jpg", "id": "<64hex>"}
  DELETE /i/<64hex>.jpg  header X-Auth-Secret: <secret>  -> 204
  GET /i/<64hex>.jpg     public read of a single object
  Everything else -> 404 (no listing, no index)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

HEX64 = re.compile(r"^[0-9a-f]{64}$")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
SECRET = os.environ.get("KCWT_META_IMAGES_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))
PUBLIC_BASE = os.environ.get("KCWT_META_IMAGES_PUBLIC_BASE", "").rstrip("/")


def _auth_ok(handler: BaseHTTPRequestHandler) -> bool:
    if not SECRET:
        return False
    got = handler.headers.get("X-Auth-Secret") or ""
    return hmac.compare_digest(got, SECRET)


class Handler(BaseHTTPRequestHandler):
    server_version = "kcwt-meta-images/0.1"

    def log_message(self, fmt: str, *args) -> None:
        # Avoid logging secrets; default log has no bodies.
        sys_stderr_write = super().log_message
        sys_stderr_write(fmt, *args)

    def _404(self) -> None:
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _401(self) -> None:
        self.send_response(401)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        m = re.fullmatch(r"/i/([0-9a-f]{64})\.jpg", path)
        if not m:
            self._404()
            return
        hex_id = m.group(1)
        fp = DATA_DIR / f"{hex_id}.jpg"
        if not fp.is_file():
            self._404()
            return
        data = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/upload":
            self._404()
            return
        if not _auth_ok(self):
            self._401()
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > 8 * 1024 * 1024:
            self.send_response(400)
            self.end_headers()
            return
        body = self.rfile.read(length)
        hex_id = secrets.token_hex(32)  # 64 hex chars
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / f"{hex_id}.jpg").write_bytes(body)
        rel = f"/i/{hex_id}.jpg"
        url = f"{PUBLIC_BASE}{rel}" if PUBLIC_BASE else rel
        payload = f'{{"id":"{hex_id}","url":"{url}"}}\n'.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        m = re.fullmatch(r"/i/([0-9a-f]{64})\.jpg", path)
        if not m:
            self._404()
            return
        if not _auth_ok(self):
            self._401()
            return
        fp = DATA_DIR / f"{m.group(1)}.jpg"
        if fp.is_file():
            fp.unlink()
        self.send_response(204)
        self.end_headers()

    def do_HEAD(self) -> None:
        # No listing via HEAD either
        self._404()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SECRET:
        print("WARN: KCWT_META_IMAGES_SECRET unset — upload/delete will 401", flush=True)
    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"kcwt-meta-images listening on :{PORT} data={DATA_DIR}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
