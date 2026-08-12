#!/usr/bin/env python3
"""Find Sony's sustainable rate ceiling for the onlineIds endpoint.
Fixed-rate windows stepping up; stop on first 403 cluster; confirm at last-clean x0.8.
Every request uses a real unverified queue name -> products results into verified_probe.json."""
import json, os, sys, time, threading, queue
import urllib.request, urllib.error

DIR = "/home/user/psn-db/data"
OUT = os.path.join(DIR, "verified_probe.json")
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
WINDOW = 25            # seconds per rate window
RATES = [3, 5, 8, 12, 18, 28, 45, 70]

res = json.load(open(OUT)) if os.path.exists(OUT) else {}
known = set(res)
# pull real queue names (skip already-verified anywhere)
import glob
for f in glob.glob(os.path.join(DIR, "verified*.json")):
    if not f.endswith("probe.json"):
        known |= set(json.load(open(f)))
todo = []
for f in ["shard1.txt", "shard2.txt", "shard3.txt", "shard4.txt"]:
    todo += [l.strip() for l in open(os.path.join(DIR, f)) if l.strip() and l.strip() not in known]
print(f"queue: {len(todo)} real names loaded", flush=True)
ti = 0
lock = threading.Lock()

def save():
    tmp = OUT + ".tmp"; json.dump(res, open(tmp, "w")); os.replace(tmp, OUT)

def do_req(name):
    req = urllib.request.Request(ENDPOINT, method="POST",
        data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return None, str(e)[:80]

results_q = queue.Queue()

def run_window(rate):
    global ti
    from concurrent.futures import ThreadPoolExecutor
    stats = {}
    end = time.time() + WINDOW
    n_workers = max(4, int(rate * 1.2))
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        next_t = time.time()
        futs = []
        while time.time() < end:
            next_t += 1.0 / rate
            d = next_t - time.time()
            if d > 0: time.sleep(d)
            if ti >= len(todo): break
            futs.append((todo[ti], pool.submit(do_req, todo[ti]))); ti += 1
        for name, f in futs:
            code, body = f.result()
            stats[code] = stats.get(code, 0) + 1
            ts = int(time.time())
            if code == 201: res[name] = {"a": 0, "why": "available", "ts": ts}
            elif code == 406: res[name] = {"a": 1, "why": "reserved3" if len(name) == 3 else "reserved", "ts": ts}
            elif code == 400: res[name] = {"a": 1, "why": "blocked" if "3208" in body else "taken", "ts": ts}
    save()
    return stats

banned_at = None; last_clean = None
for rate in RATES:
    s = run_window(rate)
    ok = sum(v for k, v in s.items() if k in (201, 400, 406))
    n403 = s.get(403, 0)
    exc = s.get(None, 0)
    print(f"[{rate:>3} rps x {WINDOW}s] ok={ok} 403={n403} exc={exc} other={ {k:v for k,v in s.items() if k not in (201,400,406,403,None)} }", flush=True)
    if n403 >= 3 or (rate >= 12 and (n403 + exc) > ok * 0.02 + 1):
        banned_at = rate
        break
    last_clean = rate

if banned_at:
    print(f"CEILING breached at {banned_at} rps. Cooling down & re-probing at 1 rps...", flush=True)
    while True:
        code, _ = do_req(todo[ti % len(todo)])
        if code != 403:
            print(f"unbanned (probe HTTP {code})", flush=True); break
        print("still banned, waiting 60s...", flush=True); time.sleep(60)

confirm = max(1, int((last_clean or 1) * 0.8))
print(f"CONFIRM hold at {confirm} rps for 180s...", flush=True)
for _ in range(6):
    s = run_window(confirm)
    print(f"  hold {confirm} rps: ok={sum(v for k,v in s.items() if k in (201,400,406))} 403={s.get(403,0)} exc={s.get(None,0)}", flush=True)
    if s.get(403, 0) >= 3:
        print(f"  -> NOT actually sustainable at {confirm} rps; drop a notch", flush=True)
        confirm = max(1, int(confirm * 0.6))
print(f"RESULT last_clean={last_clean}rps banned_at={banned_at} production_rate={confirm}rps", flush=True)
save()
