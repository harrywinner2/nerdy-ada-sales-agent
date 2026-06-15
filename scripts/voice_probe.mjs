import WebSocket from 'ws';
const URL='wss://ada-web-production.up.railway.app/ws/web';
const ws=new WebSocket(URL);
let ready=false, audioChunks=0, transcript='', gotErr=null;
const done=(ok)=>{ try{ws.close()}catch{}; 
  console.log('--- voice probe result ---');
  console.log('ready:',ready,'| audio chunks:',audioChunks,'| transcript:',JSON.stringify(transcript.slice(0,160)));
  if(gotErr)console.log('error:',gotErr);
  console.log(ok && ready && audioChunks>0 ? 'PASS: live Realtime voice pipeline works' : 'CHECK: see above');
  process.exit(0);
};
ws.on('open',()=>console.log('ws open'));
ws.on('message',d=>{
  let m; try{m=JSON.parse(d.toString())}catch{return}
  if(m.type==='ready'){ready=true; console.log('READY call_id=',m.call_id,'version=',m.version);}
  else if(m.type==='audio'){audioChunks++;}
  else if(m.type==='transcript'){ if(m.role==='agent') transcript+=m.text+' '; console.log('transcript['+m.role+']:',m.text.slice(0,120));}
  else if(m.type==='error'){gotErr=m.message; console.log('server error:',m.message);}
  if(audioChunks>5 && transcript) done(true);
});
ws.on('error',e=>{gotErr=e.message; done(false);});
setTimeout(()=>done(true), 25000);
