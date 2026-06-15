import { chromium } from 'playwright';
const BASE='https://ada-web-production.up.railway.app';
const routes=[['#/','live-prod'],['#/knowledge','kb-prod'],['#/experiments','exp-prod'],['#/overview','ov-prod']];
const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1500,height:950}});
const errs=[];
p.on('pageerror',e=>errs.push('PAGEERR:'+e.message));
p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
for(const [r,name] of routes){
  await p.goto(BASE+'/'+r,{waitUntil:'networkidle',timeout:30000}).catch(e=>console.log('nav',name,e.message));
  await new Promise(x=>setTimeout(x,1500));
  await p.screenshot({path:`design/${name}.png`});
  console.log('shot',name);
}
console.log('ERRORS:',errs.length?JSON.stringify(errs.slice(0,8)):'none');
await b.close();
