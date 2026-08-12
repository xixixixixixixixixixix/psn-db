# PSN Username Database

A Spell-style database of PSN Online ID candidates: browse, search, filter, rarity scores,
availability statuses, favourites — as a single self-contained `index.html` (no server,
no internet, no dependencies).

## Files

| File | What it is |
|---|---|
| `index.html` | **The app.** Generated, self-contained (data + code inline). Open in any browser. |
| `build.py` | The generator. Edit word lists / scoring / generation, then rerun to rebuild `index.html`. Merges `data/verified.json` automatically. |
| `check.py` | The live verifier. Sweeps names against Sony's account endpoint, incremental + resumable. |
| `data/verified.json` | Verification results so far (`{name: {a, why, ts}}`). |
| `data/all_names.txt` | Sweep queue (rarity order, best first). |
| `README.md` | This file. |

## Rebuild

```bash
python3 build.py          # bakes the latest data/verified.json into index.html
python3 check.py data/all_names.txt   # resume/extend the verification sweep
```

## The database

**500,863 candidates**, built from:

- **Full enumerated spaces** — every PSN-valid 3-char combo (37,544: letter + `[a-z0-9_-]`²) and every
  4-letter combo (456,976 = 26⁴). The complete OG-hunting territory, minus digit/underscore 4-char junk.
- **Pokémon** — all 1,025 species names (Gen 1–9, normalized to PSN-legal: `farfetchd`, `mrmime`,
  `fluttermane`…), category 14.
- **Curated lists** — dictionary words (3–16 chars), first names, acronyms, a curated OG list.
- **Generated 5–8 letter candidates** — syllable-built pronounceables, palindromes & repeats,
  keyboard patterns, digit variants, underscore/hyphen variants, random bulk filler.

Every entry passes PSN format rules: 3–16 chars, starts with a letter, only
`a-z 0-9 _ -`, no spaces (asserted at build time). Unverified-unchecked rows are stored as 3-field
compact records to keep the file at ~11 MB.

## Rarity score (0–99)

Heuristic — measures *desirability*, independent of whether the ID is taken.

- **Base by length**: 3 chars = 64 … 16 chars = 9.
- **Bonuses**: 3-letter dictionary word +24, word +14/+13/+9 by length, name +7…+18,
  acronym +8, pronounceable +8, OG style +5 (+4 more if a curated OG tag that's clean),
  notable repeat +7 (≤4 chars) / +3, letter pattern +5, balanced vowels +3.
- **Penalties**: digits −18 (or worse), underscore −14, hyphen −12, unpronounceable −10/−14,
  rare-letter clusters (q/z/x/j) −4 each — *but* these last two are waived for real words/names
  (`jazz`, `lynx` aren't punished) and intentional keyboard patterns (`asd`, `zxc`).
- Small deterministic jitter (±2) so scores don't land in identical bands.

Tiers: **S** 90–99 · **A** 80–89 · **B** 70–79 · **C** 60–69 · **Common** <60.
Current distribution ~ S 6% / A 16% / B 38% / C 13% / Common 27%.

## Availability — live-verified against Sony

Verification posts to the same endpoint the PlayStation **account-creation** (web signup) flow uses:

```
POST https://accounts.api.playstation.com/api/v1/accounts/onlineIds
{"onlineId": "<name>", "reserveIfAvailable": false}
```

| Response | Meaning |
|---|---|
| `201 {}` | **Claimable** — no account holds it, nothing was reserved (`reserveIfAvailable:false` keeps it side-effect free). Confirmed-available requires two 201s on separate requests. |
| `400` code `3101` | Taken — "Account with this online id already exists" |
| `400` code `3208` | **Blocked word** — "Improper onlineId" (e.g. `playstation`) |
| `406` | **Reserved** — two sub-classes: every 3-character ID (class-verified: 312/312 random samples returned 406; Sony no longer issues them), and trademark/policy blocks on longer names (e.g. Pokémon species `hooh`, `seel`, `muk` — Sony reserves Nintendo IP) |

**Known limitation (learned the hard way):** the PS App / console **rename** flow for existing accounts
validates through a different, stricter path — extra reserved-word and policy filters. A name can be
`201 Available` here and still be rejected there as "not available". Takeaway for claiming a verified
name: create the account through the **web signup**, not the app rename. (A rename-accurate check needs
an authenticated session — planned for the backend phase.)

Verified rows in the UI carry a solid badge with a **✓ live** tag and show the reason in the detail view.
Entries the sweep hasn't reached yet show a **dashed badge with a sim tag** — a deterministic modelled
estimate (`p_taken ≈ 0.10 + (score/100)² × 0.85`), clearly marked so it's never confused with a real result.

**Calibration findings from the first 197 verified IDs:** all 3-char IDs unissuable; common words
(`power`, `warrior`, `jungle`) and even short pronounceables (`zozaci`, `slozen`, `fedri`) are taken —
19 years of accounts ate everything remotely clean. Confirmed-available so far include `prituve`,
`jispizar`, `skenatri`, `owmzrnta` and `balm_x`.

The sweep (~11.5k IDs at a polite 1.2 s/pace ≈ 4 h) is resumable: rerun `check.py` any time, then
`build.py` to bake results into `index.html`.

## Interface

Search (`/`), sort (rarity, A–Z, length, recently checked), filters for tier, availability,
all 13 categories, character-count range, character types, favourites-only, and a
**✓ verified-only** chip for browsing just the live-checked set. Row detail modal with full metadata
(source, reason, last check), favourite toggle, copy, availability re-check.
PSN format validator (sidebar), CSV export of the current filter (up to 5,000 rows),
random pick. Favourites persist in `localStorage`.

## Roadmap (roughly the phases we discussed)

1. ✅ Database + browse/search/filter/sort + detail view + favourites
2. ✅ Availability: live verification pipeline (Sony endpoint, resumable sweep) + verified/simulated badges
3. Username generator (syllable engine + word combiner, using the scoring as a fitness function) → auto-feed the sweep
4. "Recently found available" feed (trivial once the sweep finishes: filter ✓-verified + available + sort recent)
5. Rarity leaderboards, advanced filters (regex, starts/ends-with, contains)
6. Accounts, shared/public database
7. Discord bot — only if still wanted at that point

## Live app mode (server.py)

`python3 server.py` serves index.html on :8080 plus `GET /api/check?onlineId=NAME`.
Search any valid ID (a leading `@` is stripped): if it isn't live-verified, the app
asks the server, the server checks Sony exactly like the sweep, shows the result
inline, and writes `data/verified_live.json` — the name becomes a permanent DB row
on the next `python3 build.py`. The modal "⟳ Check availability" button does a real
live check in served mode too.

Why the server is needed: Sony's endpoint rejects ANY request carrying an `Origin`
header (403) — browsers cannot call it cross-origin, so the page uses the included
server as a same-origin bridge (it sends no Origin, same as check.py).

Safety: serialised Sony calls, ≥1.6s apart, 60s global cooldown on 403/429/503,
merge-cache across all data/verified*.json (sweep results are reused, never re-hit),
3-char names short-circuited from class3.json. In file mode (index.html opened
directly) live checks are disabled with an explanatory note.

New finding: 406/"reserved" is much broader than 3-char and trademarks — real words
like root/pool and junk like bquy return it. Best explanation: IDs held after a
previous holder renamed plus policy holds. UI label widened accordingly.

## v3: honest Unknowns + built-in background scanner + auto-sync

- Anything not live-checked against Sony now renders as **Unknown** — the old
  simulated estimates are gone from the build (index.html is ~30% smaller).
- server.py now owns the whole pipeline: a background thread scans
  data/sweep_queue.txt forever (Skips anything already answered), sharing ONE
  global Sony limiter with on-demand live checks. ~2.9 req/s with
  PSN_INTERVAL=0.35 (proven-clean band is ~3-5 rps; default 0.5 if env unset).
- New verifications persist to data/verified_live.json AND stream to open pages:
  the toolbar has a Sync menu (Off / 30s / 1 min / 5 min, default 1 min, saved
  per browser) that polls /api/updates?since=TS and patches rows in place —
  Unknown entries flip to their real Sony status without a rebuild.
- Rebuild (`python3 build.py`) still bakes everything into the portable file;
  the file alone stays fully usable (file mode shows a note where sync would be).

## v4: proxy pool scanning (horizontal scaling)

Sony rate-limits per egress IP, so scale = more IPs, not more threads. Put
proxies in data/proxies.txt (one per line, http://user:pass@host:port) and
server.py spawns one self-paced worker per proxy (PSN_INTERVAL between calls,
default 0.35s ≈ 2.9 req/s per IP — the proven-clean band). Throttled nodes cool
60s; 3 strikes retires a node for the run; transport-failing nodes retire after
6 errors. Live searches keep using the direct connection, separately paced.

Throughput: ~(1 + N proxies) x 2.9 req/s  ->  4 proxies ≈ 9h, 9 ≈ 4.5h,
19 ≈ 2.2h for the remaining queue. Use residential proxies — datacenter IPs
are usually pre-banned by Akamai (they'll retire instantly). HTTPS means proxies
cannot tamper with results. /api/stats reports answered/left/node health.


## Hosting (v5)

See `deploy/HOSTING.md` — packaged lanes: **A** Cloudflare Pages drag-and-drop mirror (permanent free URL, live checks via bundled Pages Function in `deploy/functions/`, assemble with `deploy/pack.sh`), **B** GitHub Actions cron scanner + Pages auto-redeploy (`deploy/psn-scan.yml`), **C** always-on full app via `deploy/Dockerfile` / `deploy/render.yaml` (Oracle Always Free / Render / Fly / Koyeb). Quick public session URL via `cloudflared tunnel --url http://localhost:8080`.


## v6 — mirror live-verify + self-refreshing pipeline (2026-08-12)

- Public mirror: **https://aliashq.pages.dev** (Cloudflare Pages). Old URL https://psn-ids-db.pages.dev still exists but is no longer the deploy target.
- Opening ANY unverified name auto-fires a live Sony check (deploy/_worker.js /api/check). Verdicts persist to Cloudflare KV (namespace PSN_CACHE), stream to every open session via /api/updates, and are folded into the master pool by deploy/pull_kv.py on each refresh run.
- Egress reality: Sony 403s Cloudflare-tagged fetch ~90% of the time; breakthroughs happen on warm egress IPs and are now captured globally via KV. A raw-socket CONNECT+startTls proxy fallback exists in _worker.js but is defeated by workerd cert validation (SNI = proxy IP, kj/compat/tls.c++ "IP address mismatch") until Cloudflare exposes hostname control on startTls — left in as a 1-attempt canary.
- Self-refresh: deploy/cron-deploy.yml (GitHub Actions, every 30 min) = pull KV verdicts → 7-min proxy-fleet sweep → build.py → pack.sh → wrangler pages deploy. Needs repo secrets CF_API_TOKEN / CF_ACCOUNT_ID / CF_KV_NAMESPACE_ID; repo should be public (free unlimited minutes).
- Fleet: test_proxies.py revalidate → 277 working (2026-08-12 run took 723s for 4,404 candidates).
