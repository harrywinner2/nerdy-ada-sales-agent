// Record one short screen clip per narration beat against the LIVE site.
// Output: demo/clips/clip_001.webm .. clip_010.webm  (assemble_video.sh trims/loops to narration).
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'https://ada-web-production.up.railway.app';
const OUT = 'demo/clips';
fs.mkdirSync(OUT, { recursive: true });
const SIZE = { width: 1600, height: 900 };

// pick a call id that has a rich transcript/decisions for the detail beats
let callId = null;
try {
  const r = await fetch(`${BASE}/api/calls`);
  const { calls } = await r.json();
  const best = calls.filter(c => (c.kpis?.decisions || 0) > 3).sort((a,b)=>(b.kpis.decisions)-(a.kpis.decisions))[0] || calls[0];
  callId = best?.id;
} catch (e) { console.log('calls fetch warn', e.message); }
console.log('using call', callId);

const slowScroll = async (page, ms=14000) => {
  const steps = Math.floor(ms/200);
  for (let i=0;i<steps;i++){
    await page.mouse.wheel(0, 26).catch(()=>{});
    await page.waitForTimeout(200);
  }
};

// beat -> {route, action}
const beats = [
  { route:'#/',           secs:14 },                 // 1 hero
  { route:'#/',           secs:14 },                 // 2 live call (talk)
  { route:'#/',           secs:14, bottom:true },    // 3 call my phone (scroll down)
  { route:`#/calls/${callId}`, secs:18 },            // 4 decisions
  { route:'#/knowledge',  secs:16 },                 // 5 grounded KB
  { route:`#/calls/${callId}`, secs:16 },            // 6 memory/profile
  { route:'#/calls',      secs:16 },                 // 7 observability
  { route:'#/personas',   secs:16 },                 // 8 honest opponents
  { route:'#/experiments',secs:20 },                 // 9 before/after
  { route:'#/overview',   secs:16 },                 // 10 KPIs
];

const browser = await chromium.launch();
for (let i=0;i<beats.length;i++){
  const b = beats[i];
  const ctx = await browser.newContext({ viewport: SIZE, recordVideo:{ dir: OUT, size: SIZE }});
  const page = await ctx.newPage();
  await page.goto(`${BASE}/${b.route}`, { waitUntil:'networkidle', timeout:30000 }).catch(e=>console.log('nav',i+1,e.message));
  await page.waitForTimeout(1500);
  if (b.bottom) { await slowScroll(page, b.secs*1000 - 1500); }
  else { await slowScroll(page, b.secs*1000 - 1500); }
  await page.waitForTimeout(500);
  const vid = page.video();
  await ctx.close();                       // finalizes the webm
  const src = await vid.path();
  const dst = `${OUT}/clip_${String(i+1).padStart(3,'0')}.webm`;
  fs.renameSync(src, dst);
  console.log('recorded', dst);
}
await browser.close();
console.log('DONE');
