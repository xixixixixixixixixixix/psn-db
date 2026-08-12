// PSN DB mirror worker v2 — single-file Pages _worker.js (advanced mode).
//
//   GET /api/check?onlineId=X   live Sony verdict:
//       1. KV verdict cache (24h) if PSN_CACHE is bound
//       2. classwide short-circuit for 3-char IDs (empirically reserved en bloc)
//       3. direct Sony attempt — Akamai 403s Cloudflare-tainted egress, so this
//          is mostly a warmed-IP dice roll
//       4. fallback: CONNECT through the bundled residential proxy fleet over a
//          raw socket + startTls (Workers fetch() can't use CONNECT proxies)
//       verdicts (from ANY source) are written to KV -> /api/updates streams
//       them to every open session -> the mirror's taken-registry grows live
//   GET /api/updates?since=TS   KV-backed delta feed ({rows:[...]} like server.py)
//   GET /api/stats              build-time mirror totals
//
// Placeholders __ANSWERED_TOTAL__ / __BUILT_AT__ / __PROXIES__ filled by pack.sh.

import { connect } from "cloudflare:sockets";

const SONY = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds";
const SONY_HOST = "accounts.api.playstation.com";
const VALID = /^[a-z][a-z0-9_-]{2,15}$/;
const SITE = { answeredTotal: __ANSWERED_TOTAL__, builtAt: __BUILT_AT__ };
const PROXIES = __PROXIES__; // CONNECT canary list
const FWD_PROXIES = __FWD_PROXIES__; // HTTP forward proxies (do Sony TLS for us)
const KV_TTL = 7 * 86400;
let lastProxyErrs = [];      // debug: why the last request's proxies failed

// best-effort per-IP soft limit (in-memory, per isolate cold start)
const hits = new Map();
function limited(ip, max = 30, windowMs = 60000) {
  const now = Date.now();
  let h = hits.get(ip);
  if (!h || now - h.t0 > windowMs) { h = { t0: now, n: 0 }; hits.set(ip, h); }
  if (hits.size > 5000) hits.clear();
  return ++h.n > max;
}

const json = (code, obj) => new Response(JSON.stringify(obj), {
  status: code,
  headers: { "content-type": "application/json", "cache-control": "no-store" },
});

// verdict -> record shape used everywhere (matches server.py)
const VERDICTS = {
  available: { a: 0, why: "available" },
  taken:     { a: 1, why: "taken" },
  blocked:   { a: 1, why: "blocked" },
  reserved:  { a: 1, why: "reserved" },
};
function mapSony(status, body) {
  if (status === 201) return VERDICTS.available;
  if (status === 406) return VERDICTS.reserved;
  if (status === 400 && body) {
    if (body.includes("3101")) return VERDICTS.taken;
    if (body.includes("3208")) return VERDICTS.blocked;
  }
  return null; // paced / garbage / anything else: fail closed
}

/* ---------------- low-level socket helpers ---------------- */

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, rej) => setTimeout(() => rej(new Error("io_timeout")), ms)),
  ]);
}
function concatBytes(chunks) {
  let n = 0; for (const c of chunks) n += c.length;
  const out = new Uint8Array(n); let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out;
}
async function readSome(reader, chunks, needle, ms, maxBytes = 65536) {
  const deadline = Date.now() + ms;
  const td = new TextDecoder();
  while (Date.now() < deadline) {
    const { value, done } = await withTimeout(
      reader.read(), Math.max(400, deadline - Date.now()));
    if (done) break;
    if (!value) continue;
    chunks.push(value);
    if (needle) {
      let n = 0; for (const c of chunks) n += c.length;
      if (n > maxBytes) break;
      if (td.decode(concatBytes(chunks)).includes(needle)) break;
    }
  }
  return td.decode(concatBytes(chunks));
}


/* ---- Sony POST via an HTTP forward proxy (absolute-URI). The proxy does
   the TLS to Sony, so we never call startTls — this is the instant path. ---- */
async function checkViaForwardProxy(proxyUrl, name) {
  let u;
  try { u = new URL(proxyUrl.includes("://") ? proxyUrl : "http://" + proxyUrl); }
  catch (e) { return null; }
  let socket = null;
  try {
    socket = connect(
      { hostname: u.hostname, port: +(u.port || 80) },
      { secureTransport: "off" });
    await withTimeout(socket.opened, 4000);
    const body = JSON.stringify({ onlineId: name, reserveIfAvailable: false });
    const w = socket.writable.getWriter();
    await w.write(new TextEncoder().encode(
      "POST " + SONY + " HTTP/1.1\r\n" +
      "Host: " + SONY_HOST + "\r\n" +
      "Content-Type: application/json\r\nAccept: application/json\r\n" +
      "Content-Length: " + body.length + "\r\nConnection: close\r\n\r\n" + body));
    w.releaseLock();
    const raw = await readSome(socket.readable.getReader(), [], null, 7000);
    try { socket.close(); } catch (e) {}
    const m = raw.match(/^HTTP\/1\.[01] (\d{3})/);
    if (!m) {
      lastProxyErrs.push(u.hostname + " fwd no_http");
      return null;
    }
    const v = mapSony(+m[1], raw);
    if (!v) lastProxyErrs.push(u.hostname + " fwd status:" + m[1]);
    return v;
  } catch (e) {
    lastProxyErrs.push(u.hostname + " fwd " + String((e && e.message) || e).slice(0, 50));
    try { socket && socket.close(); } catch (_) {}
    return null;
  }
}

/* ---- Sony POST over a raw TLS socket (no fetch(), so no cf-* headers) ---- */
async function checkViaDirectSocket(name) {
  let socket = null;
  try {
    socket = connect({ hostname: SONY_HOST, port: 443 }, { secureTransport: "on" });
    await withTimeout(socket.opened, 6000);
    const body = JSON.stringify({ onlineId: name, reserveIfAvailable: false });
    const w = socket.writable.getWriter();
    await w.write(new TextEncoder().encode(
      "POST /api/v1/accounts/onlineIds HTTP/1.1\r\n" +
      "Host: " + SONY_HOST + "\r\n" +
      "Content-Type: application/json\r\nAccept: application/json\r\n" +
      "Content-Length: " + body.length + "\r\nConnection: close\r\n\r\n" + body));
    w.releaseLock();
    const raw = await readSome(socket.readable.getReader(), [], null, 8000);
    try { socket.close(); } catch (e) {}
    const m = raw.match(/^HTTP\/1\.[01] (\d{3})/);
    if (!m) {
      lastProxyErrs.push("direct_sock no_http " + raw.slice(0, 50).replace(/[\r\n]+/g, " "));
      return null;
    }
    lastProxyErrs.push("direct_sock status:" + m[1]);
    return mapSony(+m[1], raw);
  } catch (e) {
    lastProxyErrs.push("direct_sock " + String((e && e.message) || e).slice(0, 80));
    try { socket && socket.close(); } catch (_) {}
    return null;
  }
}

/* ---- Sony POST via one CONNECT proxy over a raw socket ---- */
async function checkViaProxy(proxyUrl, name) {
  let u;
  try { u = new URL(proxyUrl.includes("://") ? proxyUrl : "http://" + proxyUrl); }
  catch (e) { return null; }
  let socket = null;
  try {
    socket = connect(
      { hostname: u.hostname, port: +(u.port || 80) },
      { secureTransport: "starttls" });
    await withTimeout(socket.opened, 4500);

    const enc = new TextEncoder();
    let w = socket.writable.getWriter();
    const auth = u.username
      ? "Proxy-Authorization: Basic " +
        btoa(decodeURIComponent(u.username) + ":" + decodeURIComponent(u.password)) + "\r\n"
      : "";
    await w.write(enc.encode(
      "CONNECT " + SONY_HOST + ":443 HTTP/1.1\r\n" +
      auth + "\r\n"));   // byte-matches Python's http.client._tunnel (no Host line)
    w.releaseLock();
    let r = socket.readable.getReader();
    const head = await readSome(r, [], "\r\n\r\n", 6000);
    r.releaseLock();
    if (!/^HTTP\/1\.[01] 200/i.test(head)) {
      lastProxyErrs.push(u.hostname + " connect_resp:" + head.slice(0, 40).replace(/[\r\n]+/g, " "));
      socket.close(); return null;
    }

    // Without an explicit hostname, startTls validates the peer cert against
    // the PROXY address ("IP address mismatch"). Pass Sony's hostname so SNI +
    // validation target the real endpoint (silently ignored on old runtimes).
    socket = socket.startTls({ hostname: SONY_HOST }) || socket;
    w = socket.writable.getWriter();
    const body = JSON.stringify({ onlineId: name, reserveIfAvailable: false });
    await w.write(enc.encode(
      "POST /api/v1/accounts/onlineIds HTTP/1.1\r\n" +
      "Host: " + SONY_HOST + "\r\n" +
      "Content-Type: application/json\r\nAccept: application/json\r\n" +
      "Content-Length: " + body.length + "\r\nConnection: close\r\n\r\n" + body));
    w.releaseLock();
    r = socket.readable.getReader();
    const raw = await readSome(r, [], null, 9000); // connection: close -> read to EOF
    try { socket.close(); } catch (e) {}

    const m = raw.match(/^HTTP\/1\.[01] (\d{3})/);
    if (!m) return null;
    return mapSony(+m[1], raw); // tiny body; code tokens stay intact even chunked
  } catch (e) {
    lastProxyErrs.push(u.hostname + " " + String((e && e.message) || e).slice(0, 60));
    try { socket && socket.close(); } catch (_) {}
    return null;
  }
}

/* ---------------- /api/check ---------------- */
async function apiCheck(request, env, ctx) {
  const url = new URL(request.url);
  const dbg = url.searchParams.has("raw");
  const name = (url.searchParams.get("onlineId") || "")
    .trim().toLowerCase().replace(/^@+/, "").trim();

  if (!VALID.test(name))
    return json(400, { ok: 0, error: "invalid_format",
      hint: "3-16 chars, starts with a letter, letters/numbers/_/- only" });

  const kv = env && env.PSN_CACHE;
  if (kv) {
    const c = await kv.get("chk:" + name, "json").catch(() => null);
    if (c && c.ts > Date.now() / 1000 - KV_TTL)
      return json(200, { ok: 1, name, a: c.a, why: c.why, ts: c.ts,
                         n: c.n || 1, cached: true });
  }

  // classwide, empirically verified: every 3-char ID is reserved as a class
  if (name.length === 3)
    return json(200, { ok: 1, name, a: 1, why: "reserved3",
                       ts: Math.floor(Date.now() / 1000), n: 1,
                       cached: true, classwide: true });

  if (limited(request.headers.get("cf-connecting-ip") || "anon"))
    return json(429, { ok: 0, error: "cooldown", retry_after: 60 });

  let verdict = null, via = null, lastStatus = 0;
  lastProxyErrs = [];

  // 1) HTTP forward proxies — they terminate TLS to Sony for us. Instant path.
  if (FWD_PROXIES.length) {
    const start = Math.floor(Math.random() * FWD_PROXIES.length);
    const deadline = Date.now() + 9000;
    for (let i = 0; i < Math.min(5, FWD_PROXIES.length) && Date.now() < deadline; i++) {
      const v = await checkViaForwardProxy(FWD_PROXIES[(start + i) % FWD_PROXIES.length], name);
      if (v) { verdict = v; via = "fwd_proxy"; break; }
    }
  }

  // 2) raw TLS / fetch() dice-roll — CF IP, usually 403, occasional warm colo
  if (!verdict) {
    try {
      const v = await checkViaDirectSocket(name);
      if (v) { verdict = v; via = "direct_sock"; }
    } catch (e) { /* fall through */ }
  }
  if (!verdict) try {
    const r = await fetch(SONY, {
      method: "POST",
      headers: { "content-type": "application/json", "accept": "application/json" },
      body: JSON.stringify({ onlineId: name, reserveIfAvailable: false }),
      signal: AbortSignal.timeout(5000),
    });
    lastStatus = r.status;
    verdict = mapSony(r.status, await r.text());
    if (verdict) via = "direct";
  } catch (e) { /* fall through */ }

  // Not a real Sony timer. CF/Akamai 403s this edge ~90% of the time and the
  // socket-proxy path dies on workerd TLS/SNI. 600s is an advisory: don't
  // hammer a route that will not suddenly start working.
  if (!verdict) {
    if (kv)
      ctx.waitUntil(kv.put("prio:" + name, String(Math.floor(Date.now() / 1000)),
        { expirationTtl: 86400 }).catch(() => {}));
    return json(429, { ok: 0, error: "cooldown", retry_after: 90,
                       reason: "cf_egress", queued: true,
                       hint: "Sony blocks Cloudflare's IP; queued for the off-CF scanner (~2 min)",
                       ...(dbg ? { sony_status: lastStatus,
                                   proxy_errs: lastProxyErrs.slice(0, 6) } : {}) });
  }

  const ts = Math.floor(Date.now() / 1000);
  if (kv)
    ctx.waitUntil(kv.put("chk:" + name,
      JSON.stringify({ a: verdict.a, why: verdict.why, ts, n: 1 }),
      { expirationTtl: KV_TTL }).catch(() => {}));

  return json(200, { ok: 1, name, a: verdict.a, why: verdict.why, ts, n: 1,
                     cached: false, ...(dbg ? { via } : {}) });
}

/* ---------------- /api/updates (KV-backed) ---------------- */
async function apiUpdates(url, env) {
  const since = +(url.searchParams.get("since") || 0) || 0;
  const now = Math.floor(Date.now() / 1000);
  const kv = env && env.PSN_CACHE;
  if (!kv) return json(200, { ok: 1, rows: [], more: false, now });

  const list = await kv.list({ prefix: "chk:", limit: 1000 }).catch(() => null);
  if (!list || !list.keys.length) return json(200, { ok: 1, rows: [], more: false, now });

  const rows = [];
  for (const k of list.keys) {
    const v = await kv.get(k.name, "json").catch(() => null);
    if (!v || !(v.ts > since)) continue;
    rows.push({ nm: k.name.slice(4), a: v.a, why: v.why, ts: v.ts, n: v.n || 1 });
  }
  rows.sort((a, b) => a.ts - b.ts);
  return json(200, { ok: 1, rows: rows.slice(0, 5000),
                     more: list.list_complete === false, now });
}

/* ---------------- router ---------------- */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    try {
      if (path === "/api/check") return await apiCheck(request, env, ctx);
      if (path === "/api/updates") return await apiUpdates(url, env);
      if (path === "/api/stats")
        return json(200, { ok: 1, answered_total: SITE.answeredTotal,
                           scan_left: null, uptime_s: null, interval_s: null,
                           proxies_configured: PROXIES.length,
                           kv: !!(env && env.PSN_CACHE),
                           mirror: true, built_at: SITE.builtAt });
    } catch (e) {
      return json(500, { ok: 0, error: "worker_error" });
    }
    return env.ASSETS.fetch(request);
  },
};
