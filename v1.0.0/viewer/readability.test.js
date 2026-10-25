import {test} from 'node:test';import assert from 'node:assert/strict';import {Timeline} from './src/timeline.js';import {groupedSquads} from './src/tactical-overlay.js';
test('passenger count follows duplicate embark, disembark and backward seek',()=>{
 const units=[{id:1,alive:true,carrier_id:null,x_cm:0,y_cm:0},{id:2,alive:true,passenger_count:0,x_cm:0,y_cm:0}];
 const events=[{event_kind:'EMBARK_DONE',sim_tick:0,payload:{unit:1,vehicle:2}},{event_kind:'EMBARK_DONE',sim_tick:1,payload:{unit:1,vehicle:2}},{event_kind:'DISEMBARK_DONE',sim_tick:2,payload:{unit:1,vehicle:2,x_cm:20,y_cm:0}}];
 const t=new Timeline({initial:{tick:0,units,facilities:[]},final:{tick:10},events});
 assert.equal(t.at(.4).units[1].passenger_count,1);assert.equal(t.at(.6).units[1].passenger_count,0);assert.equal(t.at(.2).units[1].passenger_count,1);
});
test('group LOD hysteresis excludes mounted troops',()=>{
 const frame={squads:[{id:1,team:0,member_ids:[1,2,3]}],units:[{id:1,alive:true,x_cm:0,y_cm:0},{id:2,alive:true,x_cm:10000,y_cm:10000},{id:3,alive:true,carrier_id:99,x_cm:0,y_cm:0}]};
 assert.equal(groupedSquads(frame,.3).groups[0].count,2);assert.equal(groupedSquads(frame,.33,true).far,true);assert.equal(groupedSquads(frame,.36,true).far,false);
});
