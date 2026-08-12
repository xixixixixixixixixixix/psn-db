#!/usr/bin/env python3
"""Background Twitch scan: aaaa → aaab → … via GQL. No Sony, no proxies.

Writes data/verified_twitch.json and data/twitch_cursor.txt.
If CF_* env is set, also PUTs twitch:chk:<name> so /api/updates streams
verdicts to every open ALIAS session.

Env: TWITCH_INTERVAL (default 0.12), TWITCH_WORKERS (default 4),
     CF_ACCOUNT_ID, CF_API_TOKEN, CF_KV_NAMESPACE_ID (optional).
"""
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CURSOR = os.path.join(ROOT, "data", "twitch_cursor.txt")
OUT = os.path.join(ROOT, "data", "verified_twitch.json")
GQL = "https://gql.twitch.tv/gql"
CID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
INTERVAL = float(os.environ.get("TWITCH_INTERVAL", "0.12"))
WORKERS = max(1, int(os.environ.get("TWITCH_WORKERS", "4")))
VALID = re.compile(r"^[a-z][a-z_]{3,24}$")  # letters/_ only, 4–25, matches catalogue

AID = os.environ.get("CF_ACCOUNT_ID")
TOK = os.environ.get("CF_API_TOKEN")
NS = os.environ.get("CF_KV_NAMESPACE_ID")
KV_BASE = (
    f"https://api.cloudflare.com/client/v4/accounts/{AID}/storage/kv/namespaces/{NS}"
    if (AID and TOK and NS) else None
)

_lock = threading.Lock()
_cursor = "aaaa"
_pool = {}
_pending = {}
_last_flush = 0.0
_ok = _fail = 0


def succ(s):
    chars = list(s)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] < "z":
            chars[i] = chr(ord(chars[i]) + 1)
            for j in range(i + 1, len(chars)):
                chars[j] = "a"
            return "".join(chars)
        i -= 1
    if len(s) < 25:
        return "a" * (len(s) + 1)
    return None


def load():
    global _cursor, _pool
    try:
        s = open(CURSOR).read().strip().lower()
        if re.fullmatch(r"[a-z]{4,25}", s):
            _cursor = s
    except OSError:
        pass
    try:
        _pool = json.load(open(OUT))
    except (OSError, ValueError):
        _pool = {}


def save_cursor():
    tmp = CURSOR + ".tmp"
    with open(tmp, "w") as f:
        f.write((_cursor or "") + "\n")
    os.replace(tmp, CURSOR)


def flush(force=False):
    global _last_flush
    with _lock:
        if not _pending and not force:
            return
        if not force and time.time() - _last_flush < 2.0:
            return
        _pool.update(_pending)
        n = len(_pending)
        _pending.clear()
        tmp = OUT + ".tmp"
        json.dump(_pool, open(tmp, "w"), separators=(",", ":"))
        os.replace(tmp, OUT)
        _last_flush = time.time()
        save_cursor()
    if n:
        print(f"[twitch] flushed {n} → verified_twitch.json cursor={_cursor}", flush=True)


def next_name():
    global _cursor
    with _lock:
        while _cursor:
            if _cursor not in _pool and VALID.match(_cursor):
                n = _cursor
                _cursor = succ(_cursor)
                return n
            _cursor = succ(_cursor)
        return None


def gql(name):
    body = json.dumps({
        "query": "query($login:String!){user(login:$login){id login}}",
        "variables": {"login": name},
    }).encode()
    req = urllib.request.Request(
        GQL, method="POST", data=body,
        headers={"Client-ID": CID, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read())
    if "data" not in data or "user" not in (data.get("data") or {}):
        return None
    user = data["data"]["user"]
    return {"a": 1 if user else 0, "why": "taken" if user else "available",
            "ts": int(time.time()), "n": 1}


def kv_put(name, rec):
    if not KV_BASE:
        return
    url = KV_BASE + "/values/" + urllib.parse.quote("twitch:chk:" + name, safe="") + "?expiration_ttl=604800"
    req = urllib.request.Request(
        url, method="PUT", data=json.dumps(rec).encode(),
        headers={"Authorization": f"Bearer {TOK}", "Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except Exception:
        pass


def worker():
    global _ok, _fail
    last = 0.0
    while True:
        name = next_name()
        if name is None:
            return
        wait = last + INTERVAL - time.time()
        if wait > 0:
            time.sleep(wait)
        try:
            rec = gql(name)
            last = time.time()
        except urllib.error.HTTPError as e:
            last = time.time()
            if e.code in (403, 429, 503):
                print(f"[twitch] throttle {e.code} — cool 20s", flush=True)
                time.sleep(20)
            _fail += 1
            continue
        except Exception:
            last = time.time()
            _fail += 1
            time.sleep(2)
            continue
        if not rec:
            _fail += 1
            continue
        with _lock:
            _pending[name] = rec
            _ok += 1
            n = _ok
        kv_put(name, rec)
        if n % 100 == 0:
            print(f"[twitch] {n} new ({rec['why']}) cursor={_cursor}", flush=True)
        flush()


def run():
    load()
    print(f"[twitch] scan on — start {_cursor}, {WORKERS} workers, "
          f"{1/INTERVAL:.1f}/s each, kv={'yes' if KV_BASE else 'no'}", flush=True)
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    for t in threads:
        t.start()
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    flush(force=True)
    print(f"[twitch] done ok={_ok} fail={_fail} cursor={_cursor}", flush=True)


if __name__ == "__main__":
    run()
