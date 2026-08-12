// fast_check.js — concurrent PSN availability sweeper with adaptive rate control
// todo = shard names not yet in any verified*.json ; writes data/verified_fast.json
const fs = require('fs');
const { Agent, setGlobalDispatcher } = require('/tmp/node_modules/undici');

const DIR = '/home/user/psn-db/data/';
const OUT = DIR + 'verified_fast.json';
const CAP = parseInt(process.env.CAP || '64', 10);
setGlobalDispatcher(new Agent({ connections: CAP + 8, pipelining: 1, keepAliveTimeout: 30000, connectTimeout: 10000 }));

let res = {};
if (fs.existsSync(OUT)) res = JSON.parse(fs.readFileSync(OUT, 'utf8'));
function save() { fs.writeFileSync(OUT + '.tmp', JSON.stringify(res)); fs.renameSync(OUT + '.tmp', OUT); }

const known = new Set(Object.keys(res));
for (const f of fs.readdirSync(DIR).filter(x => /^verified.*\.json$/.test(x) && !x.endsWith('fast.json')))
  for (const k of Object.keys(JSON.parse(fs.readFileSync(DIR + f, 'utf8')))) known.add(k);

let todo = [];
for (const f of ['shard1.txt', 'shard2.txt', 'shard3.txt', 'shard4.txt'])
  todo.push(...fs.readFileSync(DIR + f, 'utf8').split('\n').filter(Boolean));
todo = [...new Set(todo)].filter(n => !known.has(n));
console.log(`todo=${todo.length}`);

let idx = 0, inFlight = 0, conc = 8;
let n201 = 0, nTaken = 0, nBlock = 0, nRes = 0, errs = 0, sinceCalm = Date.now();
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function one() {
  while (idx < todo.length) {
    if (inFlight >= conc) { await sleep(50); continue; }
    const name = todo[idx++]; inFlight++;
    try {
      const r = await fetch('https://accounts.api.playstation.com/api/v1/accounts/onlineIds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ onlineId: name, reserveIfAvailable: false }),
        signal: AbortSignal.timeout(12000),
      });
      const txt = await r.text();
      const ts = Math.floor(Date.now() / 1000);
      if (r.status === 201) { res[name] = { a: 0, why: 'available', ts }; n201++; }
      else if (r.status === 406) { res[name] = { a: 1, why: name.length === 3 ? 'reserved3' : 'reserved', ts }; nRes++; }
      else if (r.status === 400) { res[name] = { a: 1, why: txt.includes('3208') ? 'blocked' : 'taken', ts }; nTaken++; }
      else if (r.status === 429 || r.status === 503) {
        errs++; conc = Math.max(2, Math.floor(conc / 2));
        console.log(`THROTTLE http${r.status} -> conc=${conc}`); await sleep(3000);
      } else { errs++; if (errs <= 12) console.log(`HTTP${r.status} body=${txt.slice(0,120)}`); }
    } catch (e) { errs++; if (errs <= 12) console.log(`EXC ${e.name}: ${String(e.message).slice(0,120)}`); }
    inFlight--;
  }
}

(async () => {
  const t0 = Date.now(); let last = 0;
  const workers = []; for (let k = 0; k < 8; k++) workers.push(one());
  const ramp = setInterval(() => {
    if (Date.now() - sinceCalm > 25000 && conc < CAP) { conc = Math.min(CAP, conc + 6); workers.push(one()); }
  }, 5000);
  const tick = setInterval(() => {
    const done = idx, dps = (done - last) / 30; last = done;
    const rate = Math.round(dps), etaMin = rate ? Math.round((todo.length - done) / rate / 60) : '?';
    console.log(`done=${done}/${todo.length} rate=${rate}/s conc=${conc} inFlight=${inFlight} | 201:${n201} taken:${nTaken} reserved:${nRes} blocked:${nBlock} err:${errs} eta=${etaMin}min`);
  }, 30000);
  const saver = setInterval(() => { sinceCalm = Date.now(); save(); }, 15000);
  await Promise.all(workers);
  clearInterval(ramp); clearInterval(tick); clearInterval(saver); save();
  console.log('SWEEP COMPLETE', JSON.stringify({ n201, nTaken, nRes, nBlock, errs }));
})();
