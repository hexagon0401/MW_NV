import {chromium} from 'playwright-core';import fs from 'node:fs';import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1500,height:980}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const doc=JSON.parse(fs.readFileSync('public/demo.json','utf8'));doc.initial.units.forEach((u,i)=>Object.assign(u,{x_cm:45000+i%16*600,y_cm:45000+Math.floor(i/16)*600}));doc.events=[];doc.final={...doc.initial,tick:3000};doc.summary={ended:true};
 await page.route('**/demo.json',r=>r.fulfill({json:doc}));await page.goto('http://127.0.0.1:18141/viewer/');await page.waitForFunction(()=>document.querySelector('#count-a')?.textContent==='64');await page.click('#pause');
 await page.locator('#team-a .unit-button').first().click();const field=await page.locator('#field').boundingBox();await page.mouse.move(field.x+field.width/2,field.y+field.height/2);await page.waitForSelector('#tooltip:not([hidden])');assert.match(await page.locator('#tooltip').textContent(),/체력/);
 await page.screenshot({path:'../docs/self-play-v2/circles-hover.png'});await page.mouse.move(10,10);await page.waitForSelector('#tooltip',{state:'hidden'});
 await page.getByRole('button',{name:'A 본진',exact:true}).click();await page.screenshot({path:'../docs/self-play-v2/headquarters.png'});
 await page.click('#fit');await page.screenshot({path:'../docs/self-play-v2/squad-overview.png'});assert.deepEqual(errors,[]);console.log('Readability circles/hover leave/HQ/overview PASS');
}finally{await browser.close();}
