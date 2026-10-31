import test from 'node:test';import assert from 'node:assert/strict';
import {speedLabel} from './src/training.js';import {isNewReplay} from './src/latest-replay.js';
test('aggregate throughput is distinct from single replay speed',()=>{assert.match(speedLabel({aggregate_sim_speed:true,sim_speed:18,workers:3}),/합산 18 sim초\/초/);assert.equal(speedLabel({sim_speed:6}),'6×');assert.match(speedLabel({aggregate_sim_speed:true,phase:'evaluation',workers:2}),/평가 처리 —/);});
test('new replay is offered without replacing a pinned publication',()=>{const pinned='old';assert.equal(isNewReplay(pinned,[{id:'training-latest',sha256:'new'}]),true);assert.equal(pinned,'old');assert.equal(isNewReplay(pinned,[{id:'training-latest',sha256:'old'}]),false);assert.equal(isNewReplay(pinned,[]),false);});
