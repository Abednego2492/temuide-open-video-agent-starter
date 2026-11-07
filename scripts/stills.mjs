// Render a few frames as small JPEGs to check layout before a full render.
// Usage: COMP=DynamicEdit node scripts/stills.mjs 0 90 450 1200
// Optional env: ENTRY (default src/index.ts), SCALE (default 0.4), BROWSER (chrome executable path)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {mkdirSync} from 'node:fs';
import path from 'node:path';

const frames = process.argv.slice(2).map(Number);
if (!frames.length) {
  console.error('Pass frame numbers, e.g. node scripts/stills.mjs 0 90 450');
  process.exit(1);
}
const entry = path.resolve(process.env.ENTRY || 'src/index.ts');
const scale = Number(process.env.SCALE || 0.4);
const browser = process.env.BROWSER ? {browserExecutable: process.env.BROWSER, chromeMode: 'chrome-for-testing'} : {};
mkdirSync('output/stills', {recursive: true});

const serveUrl = await bundle({entryPoint: entry, publicDir: path.resolve('public')});
const composition = await selectComposition({serveUrl, id: process.env.COMP || 'DynamicEdit', ...browser});
for (const f of frames) {
  const output = `output/stills/f${String(f).padStart(5, '0')}.jpg`;
  await renderStill({composition, serveUrl, output, frame: f, imageFormat: 'jpeg', scale, ...browser});
  console.log('still', output);
}
