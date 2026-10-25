import {chromium} from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const proxy=undefined;
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,proxy,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1500,height:980},userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'});
 await page.goto(process.env.MW_NV_QA_URL??'http://127.0.0.1:18141/viewer/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelector('#training-text')?.textContent.includes('PPO'),{timeout:30000});
 assert.equal(await page.locator('#speed').inputValue(),'1');
 assert.ok((await page.locator('#field').boundingBox()).height>100);
 await page.screenshot({path:'../docs/training-enhancement/desktop.png'});
 await page.setViewportSize({width:390,height:844});
 assert.ok((await page.locator('#field').boundingBox()).height>100);
 await page.screenshot({path:'../docs/training-enhancement/mobile.png'});
 console.log('Training banner, default1x and responsive viewport PASS');
}finally{await browser.close();}
