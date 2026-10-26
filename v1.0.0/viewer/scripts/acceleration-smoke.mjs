import {chromium} from 'playwright-core';import assert from 'node:assert/strict';import fs from 'node:fs';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:2});const errors=[];page.on('pageerror',e=>errors.push(e.message));let publication='old';await page.clock.install();
 const data=JSON.parse(fs.readFileSync('public/demo.json'));data.publication_id='old';
 await page.route('**/api/matches/training-latest/view',r=>r.fulfill({json:data}));
 await page.route('**/api/matches',r=>r.fulfill({json:[{id:'training-latest',sha256:publication,scores:[10,0]}]}));
 await page.route('**/api/training',r=>r.fulfill({json:{updated_at:new Date().toISOString(),phase:'learning',aggregate_sim_speed:true,sim_speed:24,workers:2,cpu_budget:4,games:51}}));
 await page.goto('http://127.0.0.1:5173/?match=training-latest');await page.waitForSelector('canvas');await page.waitForFunction(()=>document.querySelector('#clock').textContent.includes(':'));await page.click('#pause');
 await page.waitForFunction(()=>document.querySelector('#training-text').textContent.includes('합산 24'));
 const clock=await page.locator('#clock').textContent();await page.evaluate(()=>globalThis.pinnedCanvas=document.querySelector('canvas'));
 publication='new';await page.clock.fastForward(61000);await page.getByRole('button',{name:'새 경기 보기'}).waitFor({state:'visible'});
 assert.equal(await page.locator('#clock').textContent(),clock);assert.equal(await page.evaluate(()=>globalThis.pinnedCanvas===document.querySelector('canvas')),true);
 await page.screenshot({path:'../docs/adaptive-acceleration/viewer.png'});await page.close();const mobile=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});mobile.on('pageerror',e=>errors.push(e.message));
 await mobile.route('**/api/matches/training-latest/view',r=>r.fulfill({json:data}));await mobile.route('**/api/matches',r=>r.fulfill({json:[{id:'training-latest',sha256:'old',scores:[10,0]}]}));await mobile.route('**/api/training',r=>r.fulfill({json:{updated_at:new Date().toISOString(),phase:'learning',aggregate_sim_speed:true,sim_speed:24,workers:2,cpu_budget:4,games:51}}));
 await mobile.goto('http://127.0.0.1:5173/?match=training-latest');await mobile.waitForSelector('canvas');await mobile.waitForFunction(()=>document.querySelector('#clock').textContent.includes(':'));await mobile.click('#pause');await mobile.screenshot({path:'../docs/adaptive-acceleration/mobile.png'});assert.deepEqual(errors,[]);
 fs.writeFileSync('../docs/adaptive-acceleration/browser.json',JSON.stringify({passed:true,viewports:['1440x900 DPR2','390x844'],pinned_timeline:true,new_game_button:true,aggregate_status:true,page_errors:errors},null,2)+'\n');
}finally{await browser.close();}
