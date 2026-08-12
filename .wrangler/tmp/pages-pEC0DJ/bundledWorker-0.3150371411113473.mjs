var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// ../../.wrangler/tmp/bundle-FoygaO/strip-cf-connecting-ip-header.js
function stripCfConnectingIPHeader(input, init) {
  const request = new Request(input, init);
  request.headers.delete("CF-Connecting-IP");
  return request;
}
__name(stripCfConnectingIPHeader, "stripCfConnectingIPHeader");
globalThis.fetch = new Proxy(globalThis.fetch, {
  apply(target, thisArg, argArray) {
    return Reflect.apply(target, thisArg, [
      stripCfConnectingIPHeader.apply(null, argArray)
    ]);
  }
});

// _worker.js
import { connect } from "cloudflare:sockets";
var SONY = "https://accounts.api.playstation.com/api/v1/accounts/onlineIds";
var SONY_HOST = "accounts.api.playstation.com";
var VALID = /^[a-z][a-z0-9_-]{2,15}$/;
var SITE = { answeredTotal: 53490, builtAt: 1786552876 };
var PROXIES = ["# PSN scanner proxy pool \u2014 one proxy per line (rebuilt by test_proxies.py).", "# All entries verified with a real Sony POST at harvest time. Re-run the script", "# whenever throughput drops \u2014 free proxies churn. Scanner retires dead nodes itself.", "34.69.61.247:80", "34.94.46.8:80", "165.154.162.73:8888", "64.112.184.210:3128", "34.43.46.91:443", "95.211.174.135:3128", "95.211.64.139:8889", "95.211.64.139:8888", "144.178.199.118:8443", "147.161.246.34:10498", "147.161.246.34:11653"];
var KV_TTL = 7 * 86400;
var lastProxyErrs = [];
var hits = /* @__PURE__ */ new Map();
function limited(ip, max = 30, windowMs = 6e4) {
  const now = Date.now();
  let h = hits.get(ip);
  if (!h || now - h.t0 > windowMs) {
    h = { t0: now, n: 0 };
    hits.set(ip, h);
  }
  if (hits.size > 5e3)
    hits.clear();
  return ++h.n > max;
}
__name(limited, "limited");
var json = /* @__PURE__ */ __name((code, obj) => new Response(JSON.stringify(obj), {
  status: code,
  headers: { "content-type": "application/json", "cache-control": "no-store" }
}), "json");
var VERDICTS = {
  available: { a: 0, why: "available" },
  taken: { a: 1, why: "taken" },
  blocked: { a: 1, why: "blocked" },
  reserved: { a: 1, why: "reserved" }
};
function mapSony(status, body) {
  if (status === 201)
    return VERDICTS.available;
  if (status === 406)
    return VERDICTS.reserved;
  if (status === 400 && body) {
    if (body.includes("3101"))
      return VERDICTS.taken;
    if (body.includes("3208"))
      return VERDICTS.blocked;
  }
  return null;
}
__name(mapSony, "mapSony");
function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, rej) => setTimeout(() => rej(new Error("io_timeout")), ms))
  ]);
}
__name(withTimeout, "withTimeout");
function concatBytes(chunks) {
  let n = 0;
  for (const c of chunks)
    n += c.length;
  const out = new Uint8Array(n);
  let o = 0;
  for (const c of chunks) {
    out.set(c, o);
    o += c.length;
  }
  return out;
}
__name(concatBytes, "concatBytes");
async function readSome(reader, chunks, needle, ms, maxBytes = 65536) {
  const deadline = Date.now() + ms;
  const td = new TextDecoder();
  while (Date.now() < deadline) {
    const { value, done } = await withTimeout(
      reader.read(),
      Math.max(400, deadline - Date.now())
    );
    if (done)
      break;
    if (!value)
      continue;
    chunks.push(value);
    if (needle) {
      let n = 0;
      for (const c of chunks)
        n += c.length;
      if (n > maxBytes)
        break;
      if (td.decode(concatBytes(chunks)).includes(needle))
        break;
    }
  }
  return td.decode(concatBytes(chunks));
}
__name(readSome, "readSome");
async function checkViaProxy(proxyUrl, name) {
  let u;
  try {
    u = new URL(proxyUrl.includes("://") ? proxyUrl : "http://" + proxyUrl);
  } catch (e) {
    return null;
  }
  let socket = null;
  try {
    socket = connect(
      { hostname: u.hostname, port: +(u.port || 80) },
      { secureTransport: "starttls" }
    );
    await withTimeout(socket.opened, 4500);
    const enc = new TextEncoder();
    let w = socket.writable.getWriter();
    const auth = u.username ? "Proxy-Authorization: Basic " + btoa(decodeURIComponent(u.username) + ":" + decodeURIComponent(u.password)) + "\r\n" : "";
    await w.write(enc.encode(
      "CONNECT " + SONY_HOST + ":443 HTTP/1.1\r\nHost: " + SONY_HOST + ":443\r\n" + auth + "\r\n"
    ));
    w.releaseLock();
    let r = socket.readable.getReader();
    const head = await readSome(r, [], "\r\n\r\n", 6e3);
    r.releaseLock();
    if (!/^HTTP\/1\.[01] 200/i.test(head)) {
      lastProxyErrs.push(u.hostname + " connect_resp:" + head.slice(0, 40).replace(/[\r\n]+/g, " "));
      socket.close();
      return null;
    }
    socket = socket.startTls() || socket;
    w = socket.writable.getWriter();
    const body = JSON.stringify({ onlineId: name, reserveIfAvailable: false });
    await w.write(enc.encode(
      "POST /api/v1/accounts/onlineIds HTTP/1.1\r\nHost: " + SONY_HOST + "\r\nContent-Type: application/json\r\nAccept: application/json\r\nContent-Length: " + body.length + "\r\nConnection: close\r\n\r\n" + body
    ));
    w.releaseLock();
    r = socket.readable.getReader();
    const raw = await readSome(r, [], null, 9e3);
    try {
      socket.close();
    } catch (e) {
    }
    const m = raw.match(/^HTTP\/1\.[01] (\d{3})/);
    if (!m)
      return null;
    return mapSony(+m[1], raw);
  } catch (e) {
    lastProxyErrs.push(u.hostname + " " + String(e && e.message || e).slice(0, 60));
    try {
      socket && socket.close();
    } catch (_) {
    }
    return null;
  }
}
__name(checkViaProxy, "checkViaProxy");
async function apiCheck(request, env, ctx) {
  const url = new URL(request.url);
  const dbg = url.searchParams.has("raw");
  const name = (url.searchParams.get("onlineId") || "").trim().toLowerCase().replace(/^@+/, "").trim();
  if (!VALID.test(name))
    return json(400, {
      ok: 0,
      error: "invalid_format",
      hint: "3-16 chars, starts with a letter, letters/numbers/_/- only"
    });
  const kv = env && env.PSN_CACHE;
  if (kv) {
    const c = await kv.get("chk:" + name, "json").catch(() => null);
    if (c && c.ts > Date.now() / 1e3 - KV_TTL)
      return json(200, {
        ok: 1,
        name,
        a: c.a,
        why: c.why,
        ts: c.ts,
        n: c.n || 1,
        cached: true
      });
  }
  if (name.length === 3)
    return json(200, {
      ok: 1,
      name,
      a: 1,
      why: "reserved3",
      ts: Math.floor(Date.now() / 1e3),
      n: 1,
      cached: true,
      classwide: true
    });
  if (limited(request.headers.get("cf-connecting-ip") || "anon"))
    return json(429, { ok: 0, error: "cooldown", retry_after: 60 });
  let verdict = null, via = null, lastStatus = 0;
  try {
    const r = await fetch(SONY, {
      method: "POST",
      headers: { "content-type": "application/json", "accept": "application/json" },
      body: JSON.stringify({ onlineId: name, reserveIfAvailable: false }),
      signal: AbortSignal.timeout(8e3)
    });
    lastStatus = r.status;
    verdict = mapSony(r.status, await r.text());
    if (verdict)
      via = "direct";
  } catch (e) {
  }
  if (!verdict && PROXIES.length) {
    lastProxyErrs = [];
    const start = Math.floor(Math.random() * PROXIES.length);
    const deadline = Date.now() + 12e3;
    for (let i = 0; i < PROXIES.length && i < 6 && Date.now() < deadline; i++) {
      const v = await checkViaProxy(PROXIES[(start + i) % PROXIES.length], name);
      if (v) {
        verdict = v;
        via = "proxy";
        break;
      }
    }
  }
  if (!verdict)
    return json(429, {
      ok: 0,
      error: "cooldown",
      retry_after: 600,
      ...dbg ? {
        sony_status: lastStatus,
        proxy_errs: lastProxyErrs.slice(0, 4)
      } : {}
    });
  const ts = Math.floor(Date.now() / 1e3);
  if (kv)
    ctx.waitUntil(kv.put(
      "chk:" + name,
      JSON.stringify({ a: verdict.a, why: verdict.why, ts, n: 1 }),
      { expirationTtl: KV_TTL }
    ).catch(() => {
    }));
  return json(200, {
    ok: 1,
    name,
    a: verdict.a,
    why: verdict.why,
    ts,
    n: 1,
    cached: false,
    ...dbg ? { via } : {}
  });
}
__name(apiCheck, "apiCheck");
async function apiUpdates(url, env) {
  const since = +(url.searchParams.get("since") || 0) || 0;
  const now = Math.floor(Date.now() / 1e3);
  const kv = env && env.PSN_CACHE;
  if (!kv)
    return json(200, { ok: 1, rows: [], more: false, now });
  const list = await kv.list({ prefix: "chk:", limit: 1e3 }).catch(() => null);
  if (!list || !list.keys.length)
    return json(200, { ok: 1, rows: [], more: false, now });
  const rows = [];
  for (const k of list.keys) {
    const v = await kv.get(k.name, "json").catch(() => null);
    if (!v || !(v.ts > since))
      continue;
    rows.push({ nm: k.name.slice(4), a: v.a, why: v.why, ts: v.ts, n: v.n || 1 });
  }
  rows.sort((a, b) => a.ts - b.ts);
  return json(200, {
    ok: 1,
    rows: rows.slice(0, 5e3),
    more: list.list_complete === false,
    now
  });
}
__name(apiUpdates, "apiUpdates");
var worker_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    try {
      if (path === "/api/check")
        return await apiCheck(request, env, ctx);
      if (path === "/api/updates")
        return await apiUpdates(url, env);
      if (path === "/api/stats")
        return json(200, {
          ok: 1,
          answered_total: SITE.answeredTotal,
          scan_left: null,
          uptime_s: null,
          interval_s: null,
          proxies_configured: PROXIES.length,
          kv: !!(env && env.PSN_CACHE),
          mirror: true,
          built_at: SITE.builtAt
        });
    } catch (e) {
      return json(500, { ok: 0, error: "worker_error" });
    }
    return env.ASSETS.fetch(request);
  }
};

// ../../../.npm/_npx/0eedb5afd4158ff3/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../.npm/_npx/0eedb5afd4158ff3/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// ../../.wrangler/tmp/bundle-FoygaO/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = worker_default;

// ../../../.npm/_npx/0eedb5afd4158ff3/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// ../../.wrangler/tmp/bundle-FoygaO/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof __Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
__name(__Facade_ScheduledController__, "__Facade_ScheduledController__");
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = (request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    };
    #dispatcher = (type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    };
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=bundledWorker-0.3150371411113473.mjs.map
