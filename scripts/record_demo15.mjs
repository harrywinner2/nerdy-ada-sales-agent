// Record screen clips for the 15-beat demo against the LIVE site.
// Beat 14 (architecture) is a still (clip_014.png) — skipped here.
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'https://ada-web-production.up.railway.app';
const OUT = 'demo/clips';
fs.mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1600, height: 900 };

let callId = null;
try {
  const r = await fetch(`${BASE}/api/calls`);
  const { calls } = await r.json();
  const best = calls.filter(c => (c.kpis?.decisions || 0) > 3)
                    .sort((a,b)=>(b.kpis.decisions)-(a.kpis.decisions))[0] || calls[0];
  callId = best?.id;
} catch (e) { console.log('calls fetch warn', e.message); }
console.log('using call', callId);

// id -> {route, secs, start} ; start = initial scroll offset (px) before slow scroll
const cd = `#/calls/${callId}`;
const beats = {
  1:  { route:'#/',            secs:13 },
  2:  { route:'#/',            secs:13 },
  3:  { route:'#/',            secs:15 },
  4:  { route:'#/',            secs:13, start:700 },
  5:  { route:'#/calls',       secs:13 },
  6:  { route:cd,              secs:15 },
  7:  { route:cd,              secs:15, start:500 },
  8:  { route:cd,              secs:13, start:1100 },
  9:  { route:'#/knowledge',   secs:15 },
  10: { route:cd,              secs:15 },
  11: { route:'#/overview',    secs:14 },
  12: { route:'#/personas',    secs:16 },
  13: { route:'#/experiments', secs:18 },
  // 14 = still
  15: { route:'#/',            secs:14 },
};

const browser = await chromium.launch();
for (const id of Object.keys(beats)) {
  const b = beats[id];
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo:{ dir: OUT, size: SIZE }});
  const page = await ctx.newPage();
  await page.goto(`${BASE}/${b.route}`, { waitUntil:'networkidle', timeout:30000 }).catch(e=>console.log('nav',id,e.message));
  await page.waitForTimeout(1400);
  if (b.start) { await page.mouse.wheel(0, b.start); await page.waitForTimeout(400); }
  const steps = Math.floor((b.secs*1000 - 1400)/200);
  for (let i=0;i<steps;i++){ await page.mouse.wheel(0, 20).catch(()=>{}); await page.waitForTimeout(200); }
  await page.waitForTimeout(400);
  const vid = page.video();
  await ctx.close();
  const src = await vid.path();
  const dst = `${OUT}/clip_${String(id).padStart(3,'0')}.webm`;
  fs.renameSync(src, dst);
  console.log('recorded', dst);
}
await browser.close();
console.log('DONE');
