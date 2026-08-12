#!/usr/bin/env python3
"""Pull mirror live-check verdicts from Cloudflare KV into data/verified_live.json.

Someone clicks an unknown name on psn-ids-db.pages.dev -> _worker.js checks Sony
-> verdict lands in the PSN_CACHE KV namespace. This job (run by the GitHub
Action before each rebuild) folds those into the master verified pool, so the
clicked names appear as verified rows / taken-registry entries on the next deploy.

Env: CF_ACCOUNT_ID, CF_API_TOKEN, CF_KV_NAMESPACE_ID (action skips when unset).
"""
import json
import os
import sys
import urllib.request

AID = os.environ.get("CF_ACCOUNT_ID")
TOK = os.environ.get("CF_API_TOKEN")
NS = os.environ.get("CF_KV_NAMESPACE_ID")
if not (AID and TOK and NS):
    print("pull_kv: CF_* env not set — skipping (KV not configured)")
    sys.exit(0)

BASE = f"https://api.cloudflare.com/client/v4/accounts/{AID}/storage/kv/namespaces/{NS}"
HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "..", "data", "verified_live.json")


def cget(path, raw=False):
    req = urllib.request.Request(BASE + path,
                                 headers={"Authorization": f"Bearer {TOK}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        body = r.read()
    return body if raw else json.loads(body)


def main():
    keys, cursor = [], None
    while True:
        q = "/keys?prefix=chk:&limit=1000" + (f"&cursor={cursor}" if cursor else "")
        d = cget(q)
        if not d.get("success"):
            print("pull_kv: list failed:", d.get("errors"))
            sys.exit(1)
        keys += [k["name"] for k in d["result"]]
        cursor = (d.get("result_info") or {}).get("cursor")
        if not cursor or len(d["result"]) < 1000:
            break

    try:
        pool = json.load(open(POOL))
    except (OSError, ValueError):
        pool = {}

    new = 0
    for k in keys:
        name = k[4:]
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
    print(f"pull_kv: {len(keys)} mirror verdicts read, {new} merged into verified pool")


if __name__ == "__main__":
    import urllib.parse  # noqa: E402  (kept low-import for Action boot speed)
    main()
