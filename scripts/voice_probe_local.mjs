import WebSocket from 'ws';
const ws = new WebSocket('ws://127.0.0.1:8000/ws/web');
let ready=false, audio=0, tr='', err=null;
const done=()=>{ try{ws.close()}catch{}; console.log('ready:',ready,'audio:',audio,'transcript:',JSON.stringify(tr.slice(0,180))); if(err)console.log('err:',err); console.log(ready&&audio>0?'PASS':'FAIL'); process.exit(0); };
ws.on('message',d=>{ let m; try{m=JSON.parse(d.toString())}catch{return}
  if(m.type==='ready'){ready=true; console.log('READY',m.version);}
  else if(m.type==='audio') audio++;
  else if(m.type==='transcript'){ if(m.role==='agent') tr+=m.text+' '; console.log('tr['+m.role+']',m.text.slice(0,110)); }
  else if(m.type==='error'){ err=m.message; console.log('ERR',m.message); done(); }
  if(audio>5 && tr) done(); });
ws.on('error',e=>{ err=e.message; done(); });
setTimeout(done, 20000);
