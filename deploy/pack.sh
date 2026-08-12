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
import glob, json, string, time
merged = {}
for f in glob.glob("data/verified*.json"):
    try:
        for k, v in json.load(open(f)).items():
            if isinstance(v, dict):
                merged[k] = v
    except Exception:
        pass
ans = sum(1 for v in merged.values() if v.get("a") in (0, 1) and v.get("why"))
# plus the classwide 3-char reservation (data/class3.json), unless individually recorded
AL = string.ascii_lowercase + string.digits
ans += sum(1 for a in string.ascii_lowercase for b in AL for c in AL
           if (a + b + c) not in merged)
tpl = open("deploy/_worker.js").read()
tpl = tpl.replace("__ANSWERED_TOTAL__", str(ans))
tpl = tpl.replace("__BUILT_AT__", str(int(time.time())))
# bundled proxy fleet for the worker's socket fallback (latency-sorted proxies.txt)
try:
    px = [l.strip() for l in open("data/proxies.txt")
          if l.strip() and not l.strip().startswith("#")]
except OSError:
    px = []
tpl = tpl.replace("__PROXIES__", json.dumps(px[:14]))
assert "__ANSWERED_TOTAL__" not in tpl and "__BUILT_AT__" not in tpl \
    and "__PROXIES__" not in tpl
open("deploy/site/_worker.js", "w").write(tpl)
print("mirror stats baked:", f"{ans:,}", "verified on record (incl. 3-char class);",
      f"{len(px[:14])} proxies bundled")
EOF

if command -v node >/dev/null 2>&1 && node --check "$out/_worker.js" 2>/dev/null; then
  echo "worker syntax OK"
else
  echo "WARN: _worker.js not syntax-checked"
fi
echo "packed -> $out"
