import test from 'node:test';
import assert from 'node:assert/strict';

import {filterStrategyInsights} from './src/results-filter.js';
test('strategy drilldown preserves explicit aggregate and recent-example scopes',()=>{
 const d={runs:[{learners:{PPO1:{recent:[{generation:1,execution_kind:'training',evidence_level:'observed_change'}]},PPO2:{recent:[]}}}]};
 const r=filterStrategyInsights(d,new URL('https://test/api/insights?learner=PPO1&generation=1'));
 assert.equal(r.detail_scope,'recent_examples_only');assert.deepEqual(Object.keys(r.runs[0].learners),['PPO1']);assert.equal(r.runs[0].learners.PPO1.recent.length,1);
 assert.throws(()=>filterStrategyInsights(d,new URL('https://test/api/insights?generation=-1')));
});
