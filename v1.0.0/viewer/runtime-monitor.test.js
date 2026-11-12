import {test} from 'node:test';import assert from 'node:assert/strict';import {mkdtempSync,rmSync,readFileSync} from 'node:fs';import {tmpdir} from 'node:os';import {join} from 'node:path';import {execFileSync} from 'node:child_process';import {createHmac} from 'node:crypto';
import monitor,{handle,publicHealth} from '../cloud/runtime-monitor/index.js';
function fixture(){const dir=mkdtempSync(join(tmpdir(),'mw-runtime-')),db=join(dir,'lease.sqlite');
 const python=`import sqlite3,json,sys\nd=json.loads(sys.stdin.read());c=sqlite3.connect(sys.argv[1]);c.row_factory=sqlite3.Row\nif 'schema' in d:c.executescript(d['schema']);out=None\nelse:\n r=c.execute(d['sql'],d['args']);row=r.fetchone();out=dict(row) if row else None\nc.commit();print(json.dumps(out))`;
 const query=d=>JSON.parse(execFileSync('python3',['-c',python,db],{input:JSON.stringify(d),encoding:'utf8'}));query({schema:readFileSync(new URL('../cloud/runtime-monitor/schema.sql',import.meta.url),'utf8')});
 const prepare=sql=>({sql,args:[],bind(...args){this.args=args;return this;},async first(){return query({sql:this.sql,args:this.args});}});
 return {env:{RUNTIME_HMAC_KEY:'test-key',DB:{prepare,async batch(queries){for(const q of queries)await q.first();}}},cleanup:()=>rmSync(dir,{recursive:true,force:true})};}
let sequence=0;function request(env,d,now,id){const body=JSON.stringify(d),nonce=id??'request-00000000-'+(++sequence),stamp=String(now),sig=createHmac('sha256',env.RUNTIME_HMAC_KEY).update(stamp+'\n'+nonce+'\n'+body).digest('hex');return new Request('https://monitor.test/lease',{method:'POST',body,headers:{'X-Runtime-Time':stamp,'X-Runtime-Request':nonce,'X-Runtime-Signature':sig}});}
const payload=(instance='one',action='acquire')=>({instance_id:instance,boot_id:'boot-1',run_id:'run-1',action,health:{state:'RUNNING',secret:'must-not-expose',last_progress:100}});
test('atomic lease admits one host; fencing, replay, expiry and release',async()=>{const f=fixture(),env=f.env,n=1793800000;try{
 const replies=await Promise.all(['one','two'].map(i=>handle(request(env,payload(i),n),env,n)));assert.deepEqual(replies.map(r=>r.status).sort(),[200,409]);
 assert.equal((await handle(request(env,payload('one','renew'),n+30,'repeat-0000000000'),env,n+30)).status,200);
 assert.equal((await handle(request(env,payload('one','renew'),n+30,'repeat-0000000000'),env,n+30)).status,409);
 assert.equal((await handle(request(env,payload('two','release'),n+31),env,n+31)).status,409);
 assert.equal((await handle(request(env,payload('two'),n+211),env,n+211)).status,200);
 assert.equal((await handle(request(env,payload('one','renew'),n+212),env,n+212)).status,409);
 const out=await (await handle(new Request('https://monitor.test/health'),env,n+212)).json();assert.equal(out.state,'RUNNING');assert.equal('instance_id' in out,false);assert.equal('secret' in out,false);
 }finally{f.cleanup();}});
test('authentication, stale clocks, health expiry and cron',async()=>{const f=fixture(),env=f.env,n=1793800000;try{
 assert.equal((await handle(request(env,payload(),n-100),env,n)).status,401);
 assert.equal((await handle(new Request('https://monitor.test/lease',{method:'POST',body:'{}'}),env,n)).status,401);
 await handle(request(env,payload(),n),env,n);await monitor.scheduled({},env);
 assert.equal((await (await handle(new Request('https://monitor.test/health'),env,n+91)).json()).state,'STALE');
 const offline=await (await handle(new Request('https://monitor.test/health'),env,n+301)).json();assert.equal(offline.state,'HOST_OFFLINE');assert.match(offline.next_action,/Codex/);
 assert.equal(publicHealth(null,null,n).lease_valid,false);
 }finally{f.cleanup();}});
