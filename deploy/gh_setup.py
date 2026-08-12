#!/usr/bin/env python3
"""One-shot GitHub wiring for the PSN DB refresh pipeline. Idempotent.

Uses GH_TOKEN (classic PAT, scopes: repo+workflow) from deploy/.gh.env and the
Cloudflare trio from deploy/.cf.env (+ namespace id hardcoded below from the
PSN_CACHE creation). Creates the public repo, installs Actions secrets, sets
workflow permissions, and prints what to push/dispatch next.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

env = {}
for fname in (".gh.env", ".cf.env"):
    for line in open(os.path.join(HERE, fname)):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k] = v

TOK = env["GH_TOKEN"]
CF_TOKEN = env["CLOUDFLARE_API_TOKEN"]
CF_AID = env["CLOUDFLARE_ACCOUNT_ID"]
KV_ID = "5bb5789935394bf6866169ba8595b9fb"  # PSN_CACHE, created 2026-08-12
REPO = "psn-db"


def api(method, path, body=None):
    url = "https://api.github.com" + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "bearer " + TOK,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def seal(secret):
    from nacl import encoding, public
    return public.SealedBox(
        public.PublicKey(PUBKEY, encoding.Base64Encoder())
    ).encrypt(secret.encode())


st, me = api("GET", "/user")
assert st == 200, me
login = me["login"]
print("user:", login)

st, repo = api("POST", "/user/repos", {
    "name": REPO, "private": False,
    "description": "PSN Online ID catalogue + rarity + Sony-verified availability. Site: https://psn-ids-db.pages.dev",
    "homepage": "https://psn-ids-db.pages.dev",
    "has_wiki": False, "has_projects": False,
})
if st == 201:
    print("repo created:", repo["html_url"])
elif st == 422:
    print("repo exists already — continuing")
else:
    print("repo create failed:", st, repo); sys.exit(1)

st, key = api("GET", f"/repos/{login}/{REPO}/actions/secrets/public-key")
assert st == 200, key
PUBKEY, KEY_ID = key["key"], key["key_id"]

for name, val in [("CF_API_TOKEN", CF_TOKEN), ("CF_ACCOUNT_ID", CF_AID),
                  ("CF_KV_NAMESPACE_ID", KV_ID)]:
    sealed = base64.b64encode(seal(val)).decode()
    st, out = api("PUT", f"/repos/{login}/{REPO}/actions/secrets/{name}",
                  {"encrypted_value": sealed, "key_id": KEY_ID})
    print(f"secret {name}:", st, "(set)" if st in (201, 204) else out)

st, out = api("PUT", f"/repos/{login}/{REPO}/actions/permissions/workflow",
              {"default_workflow_permissions": "write"})
print("workflow write perms:", st)

st, out = api("PUT", f"/repos/{login}/{REPO}/actions/permissions", {"enabled": True})
print("actions enabled:", st)

print("DONE — remote: https://github.com/%s/%s.git" % (login, REPO))
