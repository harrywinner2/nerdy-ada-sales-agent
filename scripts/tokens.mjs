import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 }});
await p.goto('https://www.nerdy.com', { waitUntil: 'networkidle', timeout: 45000 }).catch(()=>{});
await new Promise(r=>setTimeout(r,1500));
const data = await p.evaluate(() => {
  const colors = {}, fonts = {}, radii = {};
  const els = document.querySelectorAll('*');
  els.forEach(el => {
    const s = getComputedStyle(el);
    [s.color, s.backgroundColor].forEach(c => { if(c && c!=='rgba(0, 0, 0, 0)') colors[c]=(colors[c]||0)+1; });
    if(s.fontFamily) fonts[s.fontFamily]=(fonts[s.fontFamily]||0)+1;
    if(s.borderRadius && s.borderRadius!=='0px') radii[s.borderRadius]=(radii[s.borderRadius]||0)+1;
  });
  const top = o => Object.entries(o).sort((a,b)=>b[1]-a[1]).slice(0,12);
  // sample buttons
  const btns=[...document.querySelectorAll('button,a[class*=btn],a[class*=Button]')].slice(0,6).map(el=>{const s=getComputedStyle(el);return {bg:s.backgroundColor,color:s.color,radius:s.borderRadius,pad:s.padding,fw:s.fontWeight};});
  return { colors: top(colors), fonts: top(fonts), radii: top(radii), btns };
});
console.log(JSON.stringify(data, null, 2));
await b.close();
