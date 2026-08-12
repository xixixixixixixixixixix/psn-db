#!/usr/bin/env python3
"""
Proxy harvester/validator for the PSN scanner.

Pulls free HTTP proxy lists, then validates each candidate with a REAL Sony
endpoint POST (the only test that matters — 201/400-3101/406 = the full path
works; 403/429 = Akamai-pre-banned IP; transport error = dead). Working,
latency-sorted proxies are written to data/proxies.txt (merged with the
existing file — re-run any time; free proxies churn).

Usage:  python3 test_proxies.py            # harvest ~1200 candidates, test all
        python3 test_proxies.py 300        # only test this many (fastest first)
"""
import concurrent.futures as cf
import ipaddress
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "proxies.txt")
ENDPOINT = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds"
BODY = json.dumps({"onlineId": "storm", "reserveIfAvailable": False}).encode()  # taken -> 400/3101

SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]


def harvest():
    ips = set()
    for url in SOURCES:
        try:
            txt = urllib.request.urlopen(url, timeout=15).read().decode("utf-8", "replace")
            for m in re.findall(r"^(\d+\.\d+\.\d+\.\d+:\d+)$", txt, re.M):
                ip = m.rsplit(":", 1)[0]
                try:
                    a = ipaddress.ip_address(ip)
                    if a.is_private or a.is_loopback or a.is_unspecified or a.is_reserved or a.is_multicast:
                        continue
                except ValueError:
                    continue
                ips.add(m)
        except Exception as e:
            print(f"source failed {url}: {e}")
    return sorted(ips)


def test(p):
    t0 = time.time()
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": f"http://{p}", "https": f"http://{p}"}))
    req = urllib.request.Request(ENDPOINT, data=BODY, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with op.open(req, timeout=12) as r:
            return (p, "ok" if r.status == 201 else f"odd:{r.status}", time.time() - t0)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:80]
        if e.code == 400 and "3101" in body:
            return (p, "ok", time.time() - t0)
        if e.code == 406:
            return (p, "ok", time.time() - t0)
        return (p, f"http:{e.code}", time.time() - t0)
    except Exception:
        return (p, "dead", time.time() - t0)


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    existing = []
    if os.path.exists(OUT):
        existing = [l.strip() for l in open(OUT)
                    if l.strip() and not l.startswith("#") and ":" in (l.split("://")[-1])]
        existing = [l.split("://")[-1].split("@")[-1] for l in existing]
    cands = sorted(set(harvest()) | set(existing))
    print(f"candidates: {len(cands)}")
    if cap:
        cands = cands[:cap]
        print(f"cap -> {len(cands)}")
    t0 = time.time()
    res = list(cf.ThreadPoolExecutor(50).map(test, cands))
    ok = sorted([r for r in res if r[1] == "ok"], key=lambda r: r[2])
    print(f"tested {len(res)} in {time.time()-t0:.0f}s -> WORKING {len(ok)} · "
          f"banned {sum(1 for r in res if r[1] in ('http:403','http:429'))} · "
          f"dead {sum(1 for r in res if r[1]=='dead')}")
    header = ("# PSN scanner proxy pool — one proxy per line (rebuilt by test_proxies.py).\n"
              "# All entries verified with a real Sony POST at harvest time. Re-run the script\n"
              "# whenever throughput drops — free proxies churn. Scanner retires dead nodes itself.\n")
    with open(OUT, "w") as f:
        f.write(header)
        for p, _, _ in ok:
            f.write(p + "\n")
    print(f"wrote {len(ok)} proxies -> {OUT}")


if __name__ == "__main__":
    main()
