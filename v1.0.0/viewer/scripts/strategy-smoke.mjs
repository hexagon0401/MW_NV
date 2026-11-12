import {chromium} from 'playwright-core';import assert from 'node:assert/strict';import fs from 'node:fs';
const origin=process.env.MW_NV_SMOKE_URL??'http://127.0.0.1:5181',out='../docs/strategy-learning',errors=[];
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox'],...(origin.startsWith('https:')&&process.env.HTTPS_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{})});
try{for(const [width,height] of [[1440,900],[390,844]]){
 const page=await browser.newPage({viewport:{width,height},ignoreHTTPSErrors:true,reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',r=>r.fulfill({json:r.request().url().includes('/session')?{authenticated:false}:r.request().url().includes('/training')?{mixed_training_active:true,contract:'tactics-4',teacher_condition:'ordinary',last_completed_evaluation:96,learning_diagnostics:{PPO1:{diagnostics:{approx_kl:.01,clip_fraction:.02,explained_variance:.3},teacher:{last_imitation_kl:.002,imitation_rollbacks:1}}}}:{updated_at:new Date().toISOString(),learners:{},summary:{},recent:[],learning:[],evaluation:[]}}));
 await page.goto(origin+'/dashboard/#learning');await page.waitForFunction(()=>document.body.textContent.includes('정책 업데이트 진단 펼치기'));
 assert.ok((await page.locator('#dash-content').innerText()).includes('맵 2·3·4 혼합'));await page.locator('summary').filter({hasText:'정책 업데이트 진단'}).click();assert.ok((await page.locator('#dash-content').innerText()).includes('PPO1'));assert.ok((await page.locator('#dash-content').innerText()).includes('0.0100'));
 await page.screenshot({path:`${out}/dashboard-${width}.png`,fullPage:true});await page.close();
}assert.deepEqual(errors,[]);fs.writeFileSync(out+'/browser.json',JSON.stringify({passed:true,fixtures:true,sizes:[[1440,900],[390,844]],page_errors:errors,origin},null,2)+'\n');console.log('strategy dashboard fixtures passed');}finally{await browser.close();}
