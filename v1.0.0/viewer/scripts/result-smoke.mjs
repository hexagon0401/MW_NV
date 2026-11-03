import {chromium} from 'playwright-core';import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{const page=await browser.newPage();await page.route('**/api/**',r=>r.fulfill({json:{configured:true,authenticated:false,items:[],activities:[]}}));await page.goto('http://127.0.0.1:5184/dashboard/');const labels=await page.evaluate(async()=>{
 const {rememberReplayResult,renderReplayOptions}=await import('/src/latest-replay.js');const select=document.createElement('select');document.body.append(select);
 rememberReplayResult({publication_id:'actual967',summary:{ended:true,winner:0,scores:[0,0]},final:{mission:{mode:'elimination',combat_tickets:{0:967,1:0}}}});
 const rows=[{id:'training-latest',sha256:'actual967',mode:'training',winner:0,scores:[0,0]},{id:'training-replay-b',sha256:'b',mode:'training',winner:1,scores:[0,0]}];renderReplayOptions(select,rows,{publication:'actual967'});return [...select.options].map(o=>o.textContent);
 });assert.match(labels[0],/A 승리 · 전투 티켓 A 967 : 0 B/);assert.match(labels[1],/B 승리 · 점수 —/);assert.ok(labels.every(s=>!s.includes('0:0')));console.log('recorded victory and elimination-ticket replay labels passed Chromium');}finally{await browser.close();}
