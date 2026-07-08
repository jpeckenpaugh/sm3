#!/usr/bin/env python3
"""
genesis-sm Webbfetch Proxy — Domain-filtered HTTP forwarding.

Listens on a local port, accepts POST requests with {"url": "..."},
checks the domain against an allow list, and either forwards or denies.

Usage:
    python3 scripts/proxy.py [--port 8080] [--allow-list proxy-allow-list.json]
"""

import argparse
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path


# ─── Config ──────────────────────────────────────────────────────────────────

DEFAULT_ALLOW_LIST = Path(__file__).parent / "proxy-allow-list.json"

_allow_list = None


def load_allow_list(path: str) -> dict:
    global _allow_list
    if _allow_list is not None:
        return _allow_list
    p = Path(path)
    if p.exists():
        _allow_list = json.loads(p.read_text())
    else:
        _allow_list = {"allowed_domains": [], "allowed_prefixes": []}
    return _allow_list


def is_allowed(url: str, rules: dict) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Check allowed domains
    for d in rules.get("allowed_domains", []):
        if domain == d.lower() or domain.endswith("." + d.lower()):
            return True

    # Check allowed prefixes
    for prefix in rules.get("allowed_prefixes", []):
        if url.startswith(prefix):
            return True

    return False


# ─── HTTP Handler ────────────────────────────────────────────────────────────

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._respond(400, {"error": "Invalid JSON"})
            return

        url = data.get("url", "")
        if not url:
            self._respond(400, {"error": "Missing 'url' field"})
            return

        rules = load_allow_list(str(DEFAULT_ALLOW_LIST))
        if not is_allowed(url, rules):
            domain = urlparse(url).netloc
            print(f"  BLOCKED: {domain} — {url}")
            self._respond(403, {"error": f"Domain not allowed: {domain}"})
            return

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "genesis-sm-proxy/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                print(f"  FETCHED ({resp.status}): {url}")
                self._respond(200, {"url": url, "status": resp.status, "content": content})
        except urllib.error.HTTPError as e:
            print(f"  HTTP ERROR ({e.code}): {url}")
            self._respond(e.code, {"error": str(e), "url": url})
        except urllib.error.URLError as e:
            print(f"  CONNECTION ERROR: {url} — {e.reason}")
            self._respond(502, {"error": str(e.reason), "url": url})
        except Exception as e:
            print(f"  ERROR: {url} — {e}")
            self._respond(500, {"error": str(e), "url": url})

    def do_GET(self):
        self._respond(200, {"status": "ok", "message": "genesis-sm webfetch proxy running"})

    def _respond(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"  {args[0]} {args[1]} {args[2]}")


def main():
    parser = argparse.ArgumentParser(description="genesis-sm webfetch proxy")
    parser.add_argument("--port", type=int, default=8080, help="Listen port")
    parser.add_argument("--allow-list", default=str(DEFAULT_ALLOW_LIST), help="Path to allow list JSON")
    args = parser.parse_args()

    rules = load_allow_list(args.allow_list)
    print(f"genesis-sm webfetch proxy starting on port {args.port}")
    print(f"  Allow list: {args.allow_list}")
    print(f"  Allowed domains: {len(rules.get('allowed_domains', []))}")
    print(f"  Allowed prefixes: {len(rules.get('allowed_prefixes', []))}")
    print()

    server = HTTPServer(("0.0.0.0", args.port), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
