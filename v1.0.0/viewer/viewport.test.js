import {test} from 'node:test';import assert from 'node:assert/strict';import {visibleChunks} from './src/viewport.js';
test('viewport culls chunks outside camera',()=>{assert.equal(visibleChunks(0,0,1,384,384).length,1);assert.equal(visibleChunks(0,0,1,768,768).length,4);assert.equal(visibleChunks(-3072,0,1,384,384).length,0);});
