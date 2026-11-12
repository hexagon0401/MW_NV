import {test} from 'node:test';import assert from 'node:assert/strict';import {winnerLabel,scoreLabel,viewResult} from './src/result.js';
test('actual elimination result uses recorded A winner and tickets, not conquest 0:0 or credits',()=>{
 const r=viewResult({summary:{ended:true,winner:0,scores:{0:0,1:0}},final:{mission:{mode:'elimination',combat_tickets:{0:967,1:0},teams:{1:{credits:0}}}}});
 assert.equal(winnerLabel(r),'A 승리');assert.equal(scoreLabel(r),'전투 티켓 A 967 : 0 B');
 assert.equal(winnerLabel({...r,winner:1}),'B 승리');
});
test('conquest, flag, draw and unknown older metadata retain honest labels',()=>{
 assert.equal(scoreLabel({game_mode:'conquest',scores:[0,0]}),'A 0 : 0 B');
 assert.equal(scoreLabel({game_mode:'capture_flag',scores:[2,0]}),'탈취 점수 A 2 : 0 B');
 assert.equal(scoreLabel({mode:'training',scores:[0,0]}),'점수 —');
 assert.equal(scoreLabel({game_mode:'elimination'}),'전투 티켓 A — : — B');
 assert.equal(winnerLabel({winner:null}),'무승부');
 assert.equal(winnerLabel({winner:0,credits:[100,0]}),'A 승리');
});
