import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const p=JSON.parse(readFileSync('src/project.json','utf8'));
test('valid output dimensions',()=>{assert.ok(p.width>0&&p.height>0&&p.fps>0)});
test('unique scene identifiers',()=>{assert.equal(new Set(p.scenes.map(s=>s.id)).size,p.scenes.length)});
test('valid scene frame ranges',()=>{for(const s of p.scenes){assert.ok(s.durationFrames>0);assert.ok(s.startFrame>=0);assert.ok(s.startFrame+s.durationFrames<=p.durationFrames)}});
test('full sample timeline',()=>{assert.equal(Math.max(...p.scenes.map(s=>s.startFrame+s.durationFrames)),p.durationFrames)});
