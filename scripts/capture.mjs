import { chromium } from 'playwright';
const routes = [
  ['#/', 'live'], ['#/overview','overview'], ['#/knowledge','knowledge'],
  ['#/personas','personas'], ['#/experiments','experiments'], ['#/calls','calls']
];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1500, height: 950 }});
const errs = [];
p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
p.on('pageerror', e => errs.push('PAGEERR: '+e.message));
for (const [r,name] of routes) {
  await p.goto('http://127.0.0.1:8000/'+r, { waitUntil:'networkidle', timeout:20000 }).catch(e=>console.log('nav',name,e.message));
  await new Promise(r=>setTimeout(r,1200));
  await p.screenshot({ path:`design/app-${name}.png` });
  console.log('shot', name);
}
console.log('CONSOLE ERRORS:', errs.length ? JSON.stringify(errs.slice(0,10),null,1) : 'none');
await b.close();
