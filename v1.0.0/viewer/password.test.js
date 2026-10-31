import {test} from 'node:test';import assert from 'node:assert/strict';import {passwordGate} from './src/password.js';
test('private login requires strong configured secret, valid origin and password; signs bounded session',async()=>{
 const env={MW_NV_VIEWER_PASSWORD:'fixture-only-32-character-password'};
 assert.equal(await passwordGate(new Request('https://example.com'),{}),null);
 assert.equal((await passwordGate(new Request('https://example.com/api/matches'),env)).status,401);
 assert.match(await (await passwordGate(new Request('https://example.com'),env)).text(),/type="password"/);
 const post=(password,origin='https://example.com')=>new Request('https://example.com/login',{method:'POST',headers:{Origin:origin},body:new URLSearchParams({password})});
 assert.equal((await passwordGate(post(env.MW_NV_VIEWER_PASSWORD,'https://evil.com'),env)).status,403);
 assert.equal((await passwordGate(post('wrong'),env)).status,401);
 const response=await passwordGate(post(env.MW_NV_VIEWER_PASSWORD),env);assert.equal(response.status,303);
 const cookie=response.headers.get('set-cookie');assert.match(cookie,/HttpOnly; Secure; SameSite=Strict/);
 assert.equal(await passwordGate(new Request('https://example.com/api/matches',{headers:{Cookie:cookie.split(';')[0]}}),env),true);
 assert.notEqual(await passwordGate(new Request('https://example.com/api/matches',{headers:{Cookie:cookie.split(';')[0]}}),{MW_NV_VIEWER_PASSWORD:'rotated-password-at-least-16'}),true);
});
