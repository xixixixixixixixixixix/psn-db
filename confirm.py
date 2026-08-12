#!/usr/bin/env python3
"""
Confirmation pass for 'available' verdicts.
A name only earns a confirmed-available status after TWO 201 responses from Sony,
separated in time (default >= 60s). A conflicting second result flips the entry
back to taken. Run any time; safe to repeat.

Usage: python3 confirm.py [min_age_seconds]
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "verified.json")
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
MIN_AGE = int(sys.argv[1]) if len(sys.argv) > 1 else 60

def check(name):
    req = urllib.request.Request(
        ENDPOINT, method="POST",
        data=json.dumps({"onlineId": name, "reserveIfAvailable": False}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None

def main():
    res = json.load(open(OUT))
    now = int(time.time())
    cands = [(n, v) for n, v in res.items()
             if v.get("a") == 0 and v.get("n") != 2 and now - v.get("ts", 0) >= MIN_AGE]
    print(f"{len(cands)} single-check availables to confirm", flush=True)
    for n, v in cands:
        code = check(n)
        if code == 201:
            v["n"] = 2
            v["ts"] = now
            v["why"] = "available"
            print(f"OK {n} [confirmed x2]", flush=True)
        elif code == 400:
            body_taken = None
            v["a"] = 1; v["why"] = "taken"; v["ts"] = now; v.pop("n", None)
            print(f"FLIP {n} -> taken on second look", flush=True)
        elif code == 406:
            v["a"] = 1; v["why"] = "reserved3"; v["ts"] = now; v.pop("n", None)
            print(f"FLIP {n} -> reserved3", flush=True)
        else:
            print(f"?? {n} inconclusive (HTTP {code}), left as-is", flush=True)
        json.dump(res, open(OUT, "w"), separators=(",", ":"))
        time.sleep(1.0)
    print("CONFIRM PASS COMPLETE", flush=True)

if __name__ == "__main__":
    main()
