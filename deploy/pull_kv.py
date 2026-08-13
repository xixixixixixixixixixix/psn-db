#!/usr/bin/env python3
"""Pull PSN click-check verdicts from Cloudflare KV into data/verified_live.json.

Twitch KV is owned by twitch-refresh.yml (it already commits verified_twitch.json).
Fetching 7k+ twitch:chk: values one-by-one was hanging psn-refresh for the full
14-minute job timeout, so the PSN scan never started.

Env: CF_ACCOUNT_ID, CF_API_TOKEN, CF_KV_NAMESPACE_ID (skips when unset).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AID = os.environ.get("CF_ACCOUNT_ID")
TOK = os.environ.get("CF_API_TOKEN")
NS = os.environ.get("CF_KV_NAMESPACE_ID")
if not (AID and TOK and NS):
    print("pull_kv: CF_* env not set — skipping (KV not configured)", flush=True)
    sys.exit(0)

BASE = f"https://api.cloudflare.com/client/v4/accounts/{AID}/storage/kv/namespaces/{NS}"
HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "..", "data", "verified_live.json")
DEADLINE = time.time() + int(os.environ.get("PULL_KV_SECS", "80"))


def cget(path, raw=False):
    req = urllib.request.Request(BASE + path,
                                 headers={"Authorization": f"Bearer {TOK}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read()
    return body if raw else json.loads(body)


def list_keys(prefix):
    keys, cursor = [], None
    while time.time() < DEADLINE:
        q = f"/keys?prefix={urllib.parse.quote(prefix)}&limit=1000"
        if cursor:
            q += f"&cursor={cursor}"
        d = cget(q)
        if not d.get("success"):
            print("pull_kv: list failed:", d.get("errors"), flush=True)
            break
        keys += [k["name"] for k in d.get("result") or []]
        cursor = (d.get("result_info") or {}).get("cursor")
        if not cursor or len(d.get("result") or []) < 1000:
            break
    return keys


def main():
    print("pull_kv: listing chk: …", flush=True)
    keys = list_keys("chk:")
    print(f"pull_kv: {len(keys)} PSN keys", flush=True)

    try:
        pool = json.load(open(POOL))
    except (OSError, ValueError):
        pool = {}

    new = 0
    for i, k in enumerate(keys, 1):
        if time.time() >= DEADLINE:
            print(f"pull_kv: time box hit after {i-1}/{len(keys)}", flush=True)
            break
        name = k[4:]
        if len(name) < 5:          # 3/4-char are class-reserved
            continue
        try:
            v = json.loads(cget("/values/" + urllib.parse.quote(k), raw=True))
        except Exception:
            continue
        if not isinstance(v, dict) or "a" not in v or "why" not in v:
            continue
        old = pool.get(name)
        if old is None or v.get("ts", 0) > old.get("ts", 0):
            pool[name] = {"a": v["a"], "why": v["why"],
                          "ts": int(v.get("ts", 0)), "n": int(v.get("n", 1))}
            new += 1

    tmp = POOL + ".tmp"
    with open(tmp, "w") as f:
        json.dump(pool, f)
    os.replace(tmp, POOL)
    print(f"pull_kv: {len(keys)} PSN verdicts read, {new} merged "
          f"(twitch KV skipped — twitch-refresh owns that file)", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("pull_kv: abort", type(e).__name__, e, flush=True)
        sys.exit(0)   # never block the scan
