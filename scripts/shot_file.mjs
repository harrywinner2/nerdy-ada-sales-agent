import { chromium } from 'playwright';
const file='file://'+process.argv[2]; const out=process.argv[3];
const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
await p.goto(file,{waitUntil:'networkidle'});
await new Promise(r=>setTimeout(r,1200));
await p.screenshot({path:out});
await b.close();
console.log('shot',out);
