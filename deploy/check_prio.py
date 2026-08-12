#!/usr/bin/env python3
"""Drain the mirror's click-queue (KV prio:* keys) via the proxy fleet.

The Pages worker cannot get a Sony verdict from Cloudflare egress. Failed
click-checks write prio:<name> to KV. This job (GitHub Action, every couple
of minutes) checks those names from a non-CF IP through the proxy list and
writes chk:<name> verdicts back so /api/updates + the next click return them.

Env: CF_ACCOUNT_ID, CF_API_TOKEN, CF_KV_NAMESPACE_ID
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
    print("check_prio: CF_* env not set — skipping")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PROXY_FILE = os.path.join(ROOT, "data", "proxies.txt")
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
BASE = f"https://api.cloudflare.com/client/v4/accounts/{AID}/storage/kv/namespaces/{NS}"
VALID = __import__("re").compile(r"^[a-z][a-z0-9_\-]{2,15}$")


def cf(method, path, data=None, raw=False):
    headers = {"Authorization": f"Bearer {TOK}"}
    body = None
    if data is not None:
        if isinstance(data, (bytes, bytearray)):
            body = data
        else:
            body = data.encode() if isinstance(data, str) else json.dumps(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        out = r.read()
    return out if raw else json.loads(out) if out else {}


def list_prio():
    keys, cursor = [], None
    while True:
        q = "/keys?prefix=prio:&limit=1000" + (f"&cursor={cursor}" if cursor else "")
        d = cf("GET", q)
        if not d.get("success"):
            print("check_prio: list failed:", d.get("errors"))
            sys.exit(1)
        keys += [k["name"][5:] for k in d["result"] if k["name"].startswith("prio:")]
        cursor = (d.get("result_info") or {}).get("cursor")
        if not cursor or len(d["result"]) < 1000:
            break
    return [n for n in keys if VALID.match(n) and len(n) != 3]


def load_proxies():
    out = []
    try:
        for line in open(PROXY_FILE):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "://" not in line:
                line = "http://" + line
            out.append(line)
    except OSError:
        pass
    return out


def map_sony(code, body):
    if code == 201:
        return {"a": 0, "why": "available"}
    if code == 406:
        return {"a": 1, "why": "reserved"}
    if code == 400 and body:
        if "3101" in body:
            return {"a": 1, "why": "taken"}
        if "3208" in body:
            return {"a": 1, "why": "blocked"}
    return None


def check_one(opener, name):
    req = urllib.request.Request(
        ENDPOINT, method="POST",
        data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with opener.open(req, timeout=15) as r:
            return map_sony(r.status, r.read().decode("utf-8", "replace")), r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return map_sony(e.code, body), e.code
    except Exception as e:
        return None, str(e)


def put_verdict(name, rec):
    payload = json.dumps({"a": rec["a"], "why": rec["why"],
                          "ts": int(time.time()), "n": 1})
    # raw value put
    headers = {"Authorization": f"Bearer {TOK}", "Content-Type": "text/plain"}
    url = BASE + "/values/" + urllib.parse.quote("chk:" + name, safe="") + "?expiration_ttl=604800"
    req = urllib.request.Request(url, data=payload.encode(), method="PUT", headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def del_prio(name):
    try:
        cf("DELETE", "/values/" + urllib.parse.quote("prio:" + name, safe=""))
    except Exception:
        pass


def main():
    names = list_prio()
    if not names:
        print("check_prio: queue empty")
        return
    # newest-looking first isn't available from key list; just unique preserve order
    seen, todo = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            todo.append(n)
    print(f"check_prio: {len(todo)} name(s) queued")

    proxies = load_proxies()
    openers = []
    if proxies:
        for p in proxies[:40]:
            openers.append(urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": p, "https": p})))
    openers.append(urllib.request.build_opener())  # direct last

    ok = fail = 0
    oi = 0
    for name in todo[:80]:  # hard cap per run so a burst can't stall the cron
        rec, status = None, None
        for _ in range(min(4, len(openers))):
            opener = openers[oi % len(openers)]
            oi += 1
            rec, status = check_one(opener, name)
            if rec:
                break
            time.sleep(0.2)
        if rec:
            try:
                put_verdict(name, rec)
                del_prio(name)
                ok += 1
                print(f"  {name} -> {rec['why']} ({status})")
            except Exception as e:
                fail += 1
                print(f"  {name} kv_put failed: {e}")
        else:
            fail += 1
            print(f"  {name} no verdict ({status})")
        time.sleep(0.35)
    print(f"check_prio: wrote {ok}, leftover/fail {fail}")


if __name__ == "__main__":
    main()
