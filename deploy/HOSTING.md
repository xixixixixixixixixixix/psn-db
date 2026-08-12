# Hosting the PSN DB — free lanes

## ✅ DEPLOYED: https://psn-ids-db.pages.dev (Lane A)

Live now, deployed via wrangler with the token in `deploy/.cf.env`. Redeploy
fresh data anytime:

```bash
cd psn-db
python3 build.py && bash deploy/pack.sh
set -a && . deploy/.cf.env && set +a
npx wrangler@3 pages deploy deploy/site --project-name psn-ids-db --branch main
```

What works on the mirror: full searchable catalogue, rarity tiers, semi/final
word-form categories, taken-registry lookups (52k+ on record), instant
classwide 3-char answers, honest stats/sync stubs.

**Known limit (empirical, 2026-08-12):** Sony/Akamai hard-403s any request
tainted by Cloudflare (Workers subrequests carry unstrippable `cf-*` headers,
and datacenter ASNs are pre-paced) — the mirror's `/api/check` route works and
answers classwide/cached rows instantly, but new-name live verdicts almost
always come back `cooldown`. The UI reports that honestly. Definitive live
checks = the local app (`python3 server.py`) which uses residential egress.
**Lane B (below) is the fix for the public site**: it feeds freshly-verified
names into the mirror on a schedule, so the catalogue answers more names
outright every few hours — no live checks needed for anything already scanned.

| Lane | What you get | Live Sony checks | Scanner |
|---|---|---|---|
| **A. Cloudflare Pages (done)** | permanent URL, full DB | ⚠️ Sony blocks CF egress → `cooldown` errors | ❌ (frozen at build) |
| **B. Pages + GitHub Actions** | data refreshes itself every 6h | same ⚠️ | ✅ cron |
| **C. Local / VPS full app** | everything | ✅ residential egress | ✅ 24/7 |

## B. Self-updating mirror — Pages + GitHub Actions

```bash
cd psn-db
git init && git add -A && git commit -m "psn-db"        # push to a GitHub repo
cp deploy/psn-scan.yml .github/workflows/psn-scan.yml
bash deploy/pack.sh && cp deploy/site/_worker.js .      # Pages serves /api/* from repo root
git add -A && git commit -m "auto-scan + worker" && git push
```

Cloudflare Pages → **Connect to Git** → pick the repo → build command: *(none)*,
output dir: `/` → deploy. Every 6h the Action sweeps ~10 min through the proxy
fleet, rebuilds `index.html` + `_worker.js` stats, commits → Pages redeploys.
Free minutes: public repo = unlimited; private = 2,000/mo (the default schedule
≈ 1,200). Proxies decay over weeks — re-run `python3 test_proxies.py` when
throughput drops and push.

## C. Full app anywhere (definitive live checks)

```bash
docker build -f deploy/Dockerfile -t psn-db .   # from psn-db/
docker run -d -p 8080:8080 --name psn-db psn-db
```

- **Oracle Cloud Always Free** — 4-core ARM VM, 24 GB RAM, $0 forever (card at
  signup, never charged). Best long-term home.
- **Render free** — reads `deploy/render.yaml`; sleeps when idle (scanner idles
  too). **Fly.io / Koyeb** — same Dockerfile.
- Datacenter caveat is real (see Lane A limit): on a VM, set
  `PSN_INTERVAL=1.0` and let the proxy fleet do the scanning; if the VM's own
  egress is ASN-blocked, live checks degrade the same way — a residential
  machine (Lane C = your PC) is the gold standard.

## Expansion paths

- **Traffic:** Pages static = unlimited free bandwidth; Functions 100k req/day
  free → Workers Paid ($5/mo) beyond.
- **Verdict cache:** bind a KV namespace `PSN_CACHE` to the Pages project →
  `_worker.js` auto-caches verdicts 24h. Biggest scaling lever if it gets popular.
- **Payload growth:** `index.html` ~8 MB today; next step is `/data/*.json`
  lazy shards, or KV/D1 for the verified registry.
- **Abuse:** soft per-IP limiter already in `_worker.js` (30/min per isolate);
  add Turnstile if ever hammered.
- **Scanner scale:** more exit IPs = more checks/day, linearly.
  `python3 test_proxies.py` refreshes the fleet.

## Session URL (temporary)

While this workspace is alive the full app (with working live checks) also runs
here — but sandbox freezes between messages kill it. pages.dev never freezes.
