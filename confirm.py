#!/usr/bin/env python3
"""
Confirmation pass for PSN 'available' verdicts.

A name only earns confirmed-available after TWO 201s from Sony.
A conflicting second result flips the entry to taken/reserved/blocked.
Twitch files are never touched.

Usage: python3 confirm.py [min_age_seconds]
"""
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
MIN_AGE = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PSN_WHYS = {"available", "taken", "blocked", "reserved3", "reserved"}


def check(name):
    req = urllib.request.Request(
        ENDPOINT, method="POST",
        data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception:
        return None, ""


def verdict(name, code, body):
    if code == 201:
        return 0, "available"
    if code == 406:
        return 1, "reserved3" if len(name) == 3 else "reserved"
    if code == 400 and "3208" in body:
        return 1, "blocked"
    if code == 400:
        return 1, "taken"
    return None, None


def psn_files():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "data", "verified*.json"))):
        bn = os.path.basename(path).lower()
        if any(p in bn for p in ("twitch", "steam", "xbox", "discord")):
            continue
        out.append(path)
    return out


def main():
    now = int(time.time())
    # Dedup by name across shards; write the flip back to every file that
    # currently claims a=0 for that name, plus always into verified_live.json.
    pools = {}
    for path in psn_files():
        try:
            pools[path] = json.load(open(path))
        except (OSError, ValueError):
            pools[path] = {}

    live_path = os.path.join(HERE, "data", "verified_live.json")
    if live_path not in pools:
        pools[live_path] = {}

    seen = {}
    for path, data in pools.items():
        for n, v in data.items():
            if not isinstance(v, dict) or v.get("a") != 0:
                continue
            if v.get("why") and v.get("why") not in PSN_WHYS:
                continue
            if now - v.get("ts", 0) < MIN_AGE and v.get("n") == 2:
                continue
            old = seen.get(n)
            if old is None or v.get("ts", 0) > old[1].get("ts", 0):
                seen[n] = (path, v)

    print(f"{len(seen)} PSN available names to recheck", flush=True)
    for n, (_src, v) in sorted(seen.items()):
        code, body = check(n)
        a, why = verdict(n, code, body)
        rec = None
        if a == 0:
            rec = {"a": 0, "why": "available", "ts": now, "n": 2}
            print(f"OK {n} [confirmed x2]", flush=True)
        elif a == 1:
            rec = {"a": 1, "why": why, "ts": now}
            print(f"FLIP {n} -> {why} (HTTP {code})", flush=True)
        else:
            print(f"?? {n} inconclusive (HTTP {code}), left as-is", flush=True)
        if rec:
            for path, data in pools.items():
                if n in data or path == live_path:
                    data[n] = rec
            # persist live immediately so a crash keeps the flip
            json.dump(pools[live_path], open(live_path, "w"), separators=(",", ":"))
        time.sleep(0.45)

    for path, data in pools.items():
        tmp = path + ".tmp"
        json.dump(data, open(tmp, "w"), separators=(",", ":"))
        os.replace(tmp, path)
    print("CONFIRM PASS COMPLETE", flush=True)


if __name__ == "__main__":
    main()
