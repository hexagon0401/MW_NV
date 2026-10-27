import test from 'node:test';
import assert from 'node:assert/strict';

import {filterStrategyInsights} from './src/results-filter.js';
test('strategy drilldown preserves explicit aggregate and recent-example scopes',()=>{
 const d={runs:[{learners:{PPO1:{recent:[{generation:1,execution_kind:'training',evidence_level:'observed_change'}]},PPO2:{recent:[]}}}]};
 const r=filterStrategyInsights(d,new URL('https://test/api/insights?learner=PPO1&generation=1'));
 assert.equal(r.detail_scope,'recent_examples_only');assert.deepEqual(Object.keys(r.runs[0].learners),['PPO1']);assert.equal(r.runs[0].learners.PPO1.recent.length,1);
 assert.throws(()=>filterStrategyInsights(d,new URL('https://test/api/insights?generation=-1')));
});
import {summarizeStrategyHistory} from './src/results-filter.js';
test('historical generation summaries include old matches independently of recent examples',()=>{
 const rows=[{generation:0,learner:'PPO1',games:130,wins:80,losses:40,draws:10},{generation:1,learner:'PPO1',games:2,wins:1,losses:1,draws:0}];
 const r=summarizeStrategyHistory(rows,new URL('https://test/api/insights?generation=0&learner=PPO1'));assert.equal(r.games,130);assert.equal(r.wins,80);assert.equal(r.complete,true);
});
