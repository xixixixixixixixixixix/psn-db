#!/usr/bin/env bash
# Assemble deploy/site/ — one index.html + one _worker.js (Pages advanced mode:
# /api/* live functions, everything else static). Deploy via wrangler:
#   . deploy/.cf.env && npx wrangler@3 pages deploy deploy/site --project-name <name>
# Or drag the deploy/site folder into Cloudflare Pages -> Upload assets.
set -euo pipefail
cd "$(dirname "$0")/.."

test -f index.html || python3 build.py

out=deploy/site
rm -rf "$out"
mkdir -p "$out"
cp index.html "$out/index.html"

python3 - <<'EOF'
import glob, json, os, string, time
merged = {}
for f in glob.glob("data/verified*.json"):
    bn = os.path.basename(f).lower()
    if any(p in bn for p in ("twitch", "steam", "xbox", "discord")):
        continue
    try:
        for k, v in json.load(open(f)).items():
            if isinstance(v, dict) and (not v.get("why") or v.get("why") in
                    ("available", "taken", "blocked", "reserved3", "reserved")):
                merged[k] = v
    except Exception:
        pass
ans = sum(1 for k, v in merged.items()
          if isinstance(v, dict) and v.get("a") in (0, 1) and v.get("why")
          and len(k) >= 5)
# classwide 3-char + 4-char reservation (Sony 406)
ans += 26 ** 3 + 26 ** 4
tpl = open("deploy/_worker.js").read()
tpl = tpl.replace("__ANSWERED_TOTAL__", str(ans))
tpl = tpl.replace("__BUILT_AT__", str(int(time.time())))
# CONNECT canary list + HTTP-forward proxies (the ones that do Sony TLS for us)
def lines(path):
    try:
        return [l.strip() for l in open(path)
                if l.strip() and not l.strip().startswith("#")]
    except OSError:
        return []
px = lines("data/proxies.txt")
fwd = lines("data/fwd_proxies.txt")
tpl = tpl.replace("__PROXIES__", json.dumps(px[:14]))
tpl = tpl.replace("__FWD_PROXIES__", json.dumps(fwd[:12]))
assert "__ANSWERED_TOTAL__" not in tpl and "__BUILT_AT__" not in tpl \
    and "__PROXIES__" not in tpl and "__FWD_PROXIES__" not in tpl
open("deploy/site/_worker.js", "w").write(tpl)
print("mirror stats baked:", f"{ans:,}", "verified on record (incl. 3/4-char class);",
      f"{len(px[:14])} connect-proxies,", f"{len(fwd[:12])} forward-proxies bundled")
EOF

if command -v node >/dev/null 2>&1 && node --check "$out/_worker.js" 2>/dev/null; then
  echo "worker syntax OK"
else
  echo "WARN: _worker.js not syntax-checked"
fi
echo "packed -> $out"
