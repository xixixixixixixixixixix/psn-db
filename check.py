#!/usr/bin/env python3
"""
Verified PSN availability checker (Sony's own account endpoint).

POST https://accounts.api.playstation.com/api/v1/accounts/onlineIds
  {"onlineId": X, "reserveIfAvailable": false}
    201 -> claimable
    400 code 3101 -> taken
    400 code 3208 -> blocked word ("Improper onlineId")
    406 -> reserved class (empirically: all 3-char IDs; PSN no longer issues them)

Writes data/verified.json: {name: {"a": 0|1, "why": "taken"|"blocked"|"reserved3", "ts": epoch}}
Resumable, incremental writes, polite pacing.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", os.environ.get("PSN_OUT", "verified.json"))
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
DELAY = float(os.environ.get("PSN_DELAY", "1.2"))

def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {}

def save(d):
    tmp = OUT + ".tmp"
    json.dump(d, open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, OUT)

def check(name, retries=3):
    for attempt in range(retries):
        req = urllib.request.Request(
            ENDPOINT, method="POST",
            data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status == 201:
                    return {"a": 0, "why": "available", "ts": int(time.time())}
                return {"a": None, "why": f"http{r.status}", "ts": int(time.time())}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 400 and "3101" in body:
                return {"a": 1, "why": "taken", "ts": int(time.time())}
            if e.code == 400 and "3208" in body:
                return {"a": 1, "why": "blocked", "ts": int(time.time())}
            if e.code == 406:
                return {"a": 1, "why": "reserved3" if len(name) == 3 else "reserved", "ts": int(time.time())}
            if e.code in (429, 503, 403):  # edge ban/throttle: do NOT record, retry much later
                time.sleep(60 * (attempt + 1)); continue
            return None  # other codes: unknown, retry on a later run
        except Exception as e:
            time.sleep(5 * (attempt + 1))
    return None  # unknown after retries

def main(names_file):
    todo = [l.strip() for l in open(names_file) if l.strip()]
    res = load()
    done = sum(1 for n in todo if n in res)
    print(f"{done}/{len(todo)} already verified", flush=True)
    for n in todo:
        if n in res:
            continue
        r = check(n)
        if r is None:
            print(f"?? {n} (no result, will retry later)", flush=True); continue
        res[n] = r
        save(res)
        print(f"{'OK ' if r['a']==0 else 'X ' if r['a']==1 else '? '}{n} [{r['why']}]", flush=True)
        time.sleep(DELAY)
    print("SWEEP COMPLETE", flush=True)

if __name__ == "__main__":
    main(sys.argv[1])
