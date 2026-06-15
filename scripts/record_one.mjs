import { chromium } from 'playwright';
import fs from 'fs';
const BASE='https://ada-web-production.up.railway.app';
const OUT='demo/clips'; const SIZE={width:1600,height:900};
const route=process.argv[2]; const idx=process.argv[3];
const browser=await chromium.launch();
const ctx=await browser.newContext({viewport:SIZE,recordVideo:{dir:OUT,size:SIZE}});
const page=await ctx.newPage();
await page.goto(`${BASE}/${route}`,{waitUntil:'networkidle',timeout:30000}).catch(e=>console.log('nav',e.message));
await page.waitForTimeout(1500);
for(let i=0;i<70;i++){await page.mouse.wheel(0,24).catch(()=>{});await page.waitForTimeout(200);}
await page.waitForTimeout(500);
const vid=page.video(); await ctx.close();
const src=await vid.path();
const dst=`${OUT}/clip_${String(idx).padStart(3,'0')}.webm`;
fs.renameSync(src,dst);
console.log('recorded',dst);
await browser.close();
