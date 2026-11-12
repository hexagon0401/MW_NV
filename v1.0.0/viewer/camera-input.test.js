import {test} from 'node:test';import assert from 'node:assert/strict';import {wheelFactor} from './src/camera.js';
test('wheel zoom normalizes units and clamps isolated events',()=>{assert.equal(wheelFactor({deltaY:1,deltaMode:1}),wheelFactor({deltaY:16,deltaMode:0}));assert.ok(wheelFactor({deltaY:-20,deltaMode:0})>1);assert.equal(wheelFactor({deltaY:10000,deltaMode:2}),Math.exp(-.22));});
