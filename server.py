#!/usr/bin/env python3
"""
PSN DB app server: one process that
  1. serves index.html
  2. live-checks names on demand        GET /api/check?onlineId=X
  3. scans the sweep queue in the background — multi-worker, one egress IP each
  4. streams new verifications to the page GET /api/updates?since=TS
  5. reports scanner status               GET /api/stats

Sony's endpoint rejects any request carrying an Origin header, so browsers can't
call it directly — this server is the same-origin bridge and sends none, exactly
like check.py.

Scaling model: Sony/Akamai rate-limits PER EGRESS IP (burst bucket ~100 req,
sticky ~10 min bans after repeat trips; ~3-5 rps sustained is proven clean).
Threads don't help on one IP — exit IPs do. Put proxies in data/proxies.txt
(one per line: http://[user:pass@]host:port — residential, not datacenter) and
the scanner spawns one worker per proxy plus keeps the direct connection for
live searches. Each node self-paces at PSN_INTERVAL and cools down on its own —
workers never share an IP, so rates multiply safely.

Safety:
  - per-node serialised pacing, never faster than PSN_INTERVAL per IP
  - 403/429/503 -> that node cools down 60s, nothing recorded; 3 strikes -> node
    retired for the run (dead/bait proxy)
  - merge-cache over all data/verified*.json (mtime-checked); anything already
    answered never costs a request
  - 3-char IDs short-circuited from class3.json
  - garbage/non-Sony responses are never recorded (fail-closed)
  - disk writes batched (flush <= every 2s, immediate for live searches)

Env: PORT (8080), PSN_INTERVAL (0.35), PROXIES (path, default data/proxies.txt),
     SCAN=0 disables the scanner, PSN_WORKERS caps worker threads (default: all).
"""
import glob
import json
import os
import re
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
LIVE_OUT = os.path.join(HERE, "data", "verified_live.json")
CLASS3 = os.path.join(HERE, "data", "class3.json")
INDEX = os.path.join(HERE, "index.html")
SCAN_QUEUE = os.path.join(HERE, "data", "sweep_queue.txt")
CURSOR_FILE = os.path.join(HERE, "data", "scan_cursor.txt")
PROXY_FILE = os.environ.get("PROXIES", os.path.join(HERE, "data", "proxies.txt"))
PORT = int(os.environ.get("PORT", "8080"))
MIN_INTERVAL = float(os.environ.get("PSN_INTERVAL", "0.35"))
SCAN_ON = os.environ.get("SCAN", "1") != "0"
MAX_WORKERS = int(os.environ.get("PSN_WORKERS", "64"))
COOLDOWN = 60.0
VALID = re.compile(r"^[a-z][a-z0-9_\-]{2,15}$")

_cache = {}            # name -> record (merged verified*.json + in-memory pending)
_mtimes = {}
_io_lock = threading.Lock()
_pending = {}
_last_flush = 0.0
_c3 = None
_stats = {"started": int(time.time()), "checked": 0, "scan_total": 0, "scan_left": None,
          "scan_cursor": None, "scan_len": None}


def answered(rec):
    return rec is not None and rec.get("a") is not None


def load_cache():
    files = sorted(glob.glob(os.path.join(HERE, "data", "verified*.json")))
    cur = {}
    for f in files:
        try:
            cur[f] = os.path.getmtime(f)
        except OSError:
            pass
    with _io_lock:
        if cur == _mtimes and _cache:
            return
        merged = {}
        for f in files:
            try:
                for k, v in json.load(open(f)).items():
                    old = merged.get(k)
                    if old is None or v.get("ts", 0) > old.get("ts", 0):
                        merged[k] = v
            except Exception:
                pass
        merged.update(_pending)
        _mtimes.clear()
        _mtimes.update(cur)
        _cache.clear()
        _cache.update(merged)


def _flush():
    global _last_flush
    with _io_lock:
        if not _pending:
            return
        live = {}
        if os.path.exists(LIVE_OUT):
            try:
                live = json.load(open(LIVE_OUT))
            except Exception:
                live = {}
        live.update(_pending)
        n = len(_pending)
        _pending.clear()
        tmp = LIVE_OUT + ".tmp"
        json.dump(live, open(tmp, "w"), separators=(",", ":"))
        os.replace(tmp, LIVE_OUT)
        _last_flush = time.time()
    print(f"[persist] flushed {n} record(s) -> verified_live.json", flush=True)


def record(name, rec, urgent=False):
    with _io_lock:
        _cache[name] = rec
        _pending[name] = rec
    if urgent or time.time() - _last_flush > 2.0:
        _flush()
    _stats["checked"] += 1


def class3():
    global _c3
    if _c3 is None and os.path.exists(CLASS3):
        try:
            _c3 = json.load(open(CLASS3))
        except Exception:
            _c3 = {}
    return _c3 or {}


# ---------------------------------------------------------------- egress nodes
class Node:
    """One egress IP (direct connection or one proxy) with its own pacer/cooldown."""
    def __init__(self, label, proxy_url=None):
        self.label = label
        self.proxy_url = proxy_url
        if proxy_url:
            self.opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
        else:
            self.opener = urllib.request.build_opener()
        self.lock = threading.Lock()
        self.last = 0.0
        self.cooldown_until = 0.0
        self.fails = 0
        self.ok = 0
        self.dead = False

    def _http(self, name):
        """One raw Sony POST via this node's egress. Returns (record, (err_kind, secs))."""
        req = urllib.request.Request(
            ENDPOINT, method="POST",
            data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self.opener.open(req, timeout=20) as r:
                if r.status == 201:
                    return {"a": 0, "why": "available", "ts": int(time.time())}, None
                return None, ("http%d" % r.status, 0)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 400 and "3101" in body:
                return {"a": 1, "why": "taken", "ts": int(time.time())}, None
            if e.code == 400 and "3208" in body:
                return {"a": 1, "why": "blocked", "ts": int(time.time())}, None
            if e.code == 406:
                return {"a": 1, "why": "reserved3" if len(name) == 3 else "reserved",
                        "ts": int(time.time())}, None
            if e.code in (403, 429, 503):
                return None, ("throttle", int(COOLDOWN))
            return None, ("http%d" % e.code, 0)
        except Exception as e:
            return None, ("net_" + type(e).__name__, 0)

    def check(self, name, urgent=False):
        """Paced, cache-race-safe check through this node."""
        with self.lock:
            if self.dead:
                return None, ("node_dead", 0)
            cur = _cache.get(name)
            if answered(cur):
                return cur, None
            now = time.time()
            if now < self.cooldown_until:
                return None, ("cooldown", int(self.cooldown_until - now) + 1)
            wait = self.last + MIN_INTERVAL - now
            if wait > 0:
                time.sleep(wait)
            rec, err = self._http(name)
            self.last = time.time()
            if rec is not None:
                self.ok += 1
                self.fails = max(0, self.fails - 1)
                record(name, rec, urgent)
                return rec, None
            kind, secs = err if err else ("no_result", 0)
            if kind == "throttle":
                self.cooldown_until = time.time() + COOLDOWN
                self.fails += 1
                print(f"[node:{self.label}] throttled — cool 60s (fails={self.fails})", flush=True)
                if self.fails >= 3:
                    self.dead = True
                    print(f"[node:{self.label}] 3 strikes — node retired this run", flush=True)
            elif kind.startswith("net_") or kind == "no_result":
                self.fails += 1
                if self.fails >= 6:
                    self.dead = True
                    print(f"[node:{self.label}] too many transport errors — retired ({kind})", flush=True)
            return None, (kind, secs)


DIRECT = Node("direct")


def load_nodes():
    """Direct node + one node per proxy line."""
    nodes = []
    if os.path.exists(PROXY_FILE):
        for line in open(PROXY_FILE):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "://" not in line:
                line = "http://" + line
            nodes.append(Node("proxy:" + line.split("@")[-1][:40], line))
    return nodes


# ---------------------------------------------------------------- systematic scanner (aaaa, aaab, … then 5-char, up to 16)
# 3-char is class-reserved and skipped. Letter-only ids are generated in order.
# Catalogue names with digits/_/- of a finished length are drained before bumping.
_cursor = "aaaa"
_cursor_lock = threading.Lock()
_pending_extras = []
_extras_by_len = {}
_last_cursor_save = 0.0


def succ_letter(s):
    """Next a-z id: aaaa → aaab → … → aaaz → aaba → … → zzzz → aaaaa."""
    chars = list(s)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] < "z":
            chars[i] = chr(ord(chars[i]) + 1)
            for j in range(i + 1, len(chars)):
                chars[j] = "a"
            return "".join(chars)
        i -= 1
    if len(s) < 16:
        return "a" * (len(s) + 1)
    return None


def load_cursor():
    global _cursor
    try:
        s = open(CURSOR_FILE).read().strip().lower()
    except OSError:
        return
    if re.fullmatch(r"[a-z]{4,16}", s):
        _cursor = s


def save_cursor(force=False):
    global _last_cursor_save
    now = time.time()
    if not force and now - _last_cursor_save < 2.0:
        return
    tmp = CURSOR_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write((_cursor or "") + "\n")
    os.replace(tmp, CURSOR_FILE)
    _last_cursor_save = now
    _stats["scan_cursor"] = _cursor
    _stats["scan_len"] = len(_cursor) if _cursor else None


def load_extras():
    """Non-letter catalogue names, grouped by length, already (len, a-z) sorted."""
    global _extras_by_len
    by = {n: [] for n in range(4, 17)}
    try:
        for line in open(SCAN_QUEUE):
            n = line.strip().lower()
            if (4 <= len(n) <= 16 and not n.isalpha() and VALID.match(n)
                    and not any(c.isdigit() for c in n)):
                by[len(n)].append(n)
    except OSError:
        pass
    _extras_by_len = by


def _advance_locked():
    """Move _cursor one step; if length bumps, queue extras of the finished length."""
    global _cursor
    old = _cursor
    nxt = succ_letter(old) if old else None
    if old and (nxt is None or len(nxt) > len(old)):
        extras = [n for n in _extras_by_len.get(len(old), [])
                  if not answered(_cache.get(n))]
        _pending_extras.extend(extras)
        if extras:
            print(f"[scan] len {len(old)} letters done — {len(extras)} digit/_/- extras",
                  flush=True)
    _cursor = nxt


def next_work():
    """Next name in aaaa, aaab, … order. None once 16-char letters are exhausted."""
    with _cursor_lock:
        while _pending_extras:
            n = _pending_extras.pop(0)
            if not answered(_cache.get(n)):
                return n
        while _cursor and answered(_cache.get(_cursor)):
            _advance_locked()
        if _pending_extras:
            n = _pending_extras.pop(0)
            save_cursor()
            return n
        if not _cursor:
            save_cursor(force=True)
            return None
        n = _cursor
        _advance_locked()
        save_cursor()
        _stats["scan_cursor"] = _cursor
        _stats["scan_len"] = len(_cursor) if _cursor else len(n)
        return n


def scanner():
    load_cursor()
    load_extras()
    _stats["scan_cursor"] = _cursor
    _stats["scan_len"] = len(_cursor) if _cursor else None
    nodes = load_nodes()[:MAX_WORKERS]
    extra_n = sum(len(v) for v in _extras_by_len.values())
    print(f"[scan] lex mode — start {_cursor} (len {len(_cursor) if _cursor else '-'}); "
          f"3-char skipped (class reserved); {extra_n} digit/_/- extras after each length",
          flush=True)
    print(f"[scan] on — {len(nodes)} proxy node(s) + direct for live checks; "
          f"~{1/MIN_INTERVAL:.1f} req/s per IP", flush=True)
    if nodes:
        print(f"[scan] aggregate ceiling ~{(len(nodes))/MIN_INTERVAL:.1f} req/s "
              f"(per-IP safe: never faster per node)", flush=True)

    passno = 0
    while True:
        passno += 1
        done_pass = [0]
        t0 = time.time()
        stop = {"done": False}

        def worker(node):
            while not stop["done"]:
                n = next_work()
                if n is None:
                    stop["done"] = True
                    return
                if answered(_cache.get(n)):
                    continue
                rec, err = node.check(n)
                if rec is not None:
                    done_pass[0] += 1
                    if done_pass[0] % 200 == 0:
                        rate = done_pass[0] / max(1.0, time.time() - t0)
                        print(f"[scan] {done_pass[0]} new ({rate:.2f}/s) cursor={_cursor}",
                              flush=True)
                else:
                    if err and err[0] == "cooldown":
                        time.sleep(min(45, err[1]))
                    elif err and err[0] in ("no_result",):
                        time.sleep(2)
                    else:
                        time.sleep(5)

        if not nodes:
            worker(DIRECT)
        else:
            threads = [threading.Thread(target=worker, args=(nd,), daemon=True)
                       for nd in nodes]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        _flush()
        save_cursor(force=True)
        rate = done_pass[0] / max(1.0, time.time() - t0)
        if _cursor is None and not _pending_extras:
            print(f"[scan] a-z space 4–16 exhausted ({done_pass[0]} this pass, "
                  f"{rate:.2f}/s). Idle 15 min.", flush=True)
            time.sleep(900)
            load_cache()
            continue
        print(f"[scan] pass {passno} done: {done_pass[0]} new ({rate:.2f}/s) "
              f"cursor={_cursor}. Continuing in 5s.", flush=True)
        time.sleep(5)


# ---------------------------------------------------------------- http layer
class Handler(BaseHTTPRequestHandler):
    server_version = "PSNDB/4.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/check":
            return self.api_check(u)
        if u.path == "/api/updates":
            return self.api_updates(u)
        if u.path == "/api/stats":
            return self.api_stats()
        if u.path in ("/", "/index.html"):
            try:
                body = open(INDEX, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except OSError:
                self._json(404, {"ok": 0, "error": "index_missing"})
            return
        self._json(404, {"ok": 0, "error": "not_found"})

    def api_check_twitch(self, name):
        if not re.fullmatch(r"[a-z][a-z0-9_]{3,24}", name):
            return self._json(400, {"ok": 0, "error": "invalid_format",
                                    "hint": "Twitch: 4–25 chars, letter first, letters/numbers/_ only"})
        body = json.dumps({
            "query": "query($login:String!){user(login:$login){id login}}",
            "variables": {"login": name},
        }).encode()
        req = urllib.request.Request(
            "https://gql.twitch.tv/gql", method="POST", data=body,
            headers={"Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read())
        except Exception as e:
            return self._json(502, {"ok": 0, "error": "twitch_unreachable",
                                    "hint": type(e).__name__})
        user = (data.get("data") or {}).get("user")
        if "data" not in data or "user" not in (data.get("data") or {}):
            return self._json(502, {"ok": 0, "error": "twitch_bad_response"})
        rec = {"a": 1 if user else 0, "why": "taken" if user else "available",
               "ts": int(time.time()), "n": 1}
        return self._json(200, {"ok": 1, "name": name, "a": rec["a"], "why": rec["why"],
                                "ts": rec["ts"], "n": 1, "cached": False, "platform": "twitch"})

    def api_check(self, u):
        load_cache()
        qs = parse_qs(u.query)
        if (qs.get("platform", ["psn"])[0] or "psn").lower() == "twitch":
            raw = (qs.get("onlineId", [""])[0] or "")
            return self.api_check_twitch(raw.strip().lower().lstrip("@").strip())
        raw = (qs.get("onlineId", [""])[0] or "")
        name = raw.strip().lower().lstrip("@").strip()
        if not VALID.match(name):
            return self._json(400, {"ok": 0, "error": "invalid_format",
                                    "hint": "3-16 chars, starts with a letter, letters/numbers/_/- only"})
        if len(name) == 3:
            c3 = class3()
            if c3:
                return self._json(200, {"ok": 1, "name": name, "a": 1, "why": "reserved3",
                                        "ts": c3.get("ts", 0), "n": 1, "cached": True,
                                        "classwide": True})
        rec = _cache.get(name)
        if answered(rec):
            return self._json(200, {"ok": 1, "name": name, "a": rec["a"], "why": rec["why"],
                                    "ts": rec["ts"], "n": rec.get("n", 1), "cached": True})
        rec, err = DIRECT.check(name, urgent=True)      # live checks go direct, paced
        if rec is not None:
            print(f"[live] {name} -> {rec['why']}", flush=True)
            return self._json(200, {"ok": 1, "name": name, "a": rec["a"], "why": rec["why"],
                                    "ts": rec["ts"], "n": rec.get("n", 1), "cached": False})
        kind, retry = err if err else ("no_result", 0)
        code = 429 if kind in ("cooldown",) else 502
        return self._json(code, {"ok": 0, "error": kind, "retry_after": retry})

    def api_updates(self, u):
        load_cache()
        try:
            since = int(parse_qs(u.query).get("since", ["0"])[0])
        except ValueError:
            since = 0
        fresh = [(v["ts"], k, v) for k, v in _cache.items()
                 if answered(v) and v.get("ts", 0) > since]
        fresh.sort()
        more = len(fresh) > 5000
        fresh = fresh[:5000]
        rows = [{"nm": k, "a": v["a"], "why": v["why"], "ts": v["ts"], "n": v.get("n", 1)}
                for _, k, v in fresh]
        return self._json(200, {"ok": 1, "rows": rows, "more": more,
                                "now": int(time.time())})

    def api_stats(self):
        nodes = load_nodes()
        left = _stats.get("scan_left")
        up = int(time.time()) - _stats["started"]
        return self._json(200, {
            "ok": 1,
            "answered_total": sum(1 for v in _cache.values() if answered(v)),
            "scan_left": left,
            "uptime_s": up,
            "interval_s": MIN_INTERVAL,
            "proxies_configured": len(nodes),
            "direct": {"ok": DIRECT.ok, "fails": DIRECT.fails,
                       "dead": DIRECT.dead,
                       "cooldown_in": max(0, int(DIRECT.cooldown_until - time.time()))},
            "scan_cursor": _stats.get("scan_cursor") or _cursor,
            "scan_len": _stats.get("scan_len") or (len(_cursor) if _cursor else None),
            "scan_mode": "lex",
        })


def main():
    def _shutdown(*_):
        try:
            save_cursor(force=True)
            _flush()
        except Exception:
            pass
        os._exit(0)
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    load_cache()
    if SCAN_ON:
        threading.Thread(target=scanner, daemon=True).start()
        def _twitch():
            try:
                sys.path.insert(0, os.path.join(HERE, "deploy"))
                import twitch_scan
                twitch_scan.run()
            except Exception as e:
                print(f"[twitch] scanner failed to start: {e}", flush=True)
        threading.Thread(target=_twitch, daemon=True).start()
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"PSN DB app server on 0.0.0.0:{PORT} — /api/check /api/updates /api/stats", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
