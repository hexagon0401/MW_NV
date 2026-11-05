import {test} from 'node:test';import assert from 'node:assert/strict';import {describeTraining} from './src/training.js';
test('training report distinguishes unavailable and stale reports',()=>{
 assert.match(describeTraining(null),/확인 불가/);
 const d={updated_at:'2026-10-25T00:00:00Z',round:2,completed_steps:256,policy_steps:300,sim_speed:25,maps:'4 variants'};
 assert.match(describeTraining(d,Date.parse(d.updated_at)),/PPO 학습 중/);
 assert.match(describeTraining(d,Date.parse(d.updated_at)+181000),/마지막 보고/);
});
