import { writeFileSync } from 'node:fs';

// The web client hands Monaco a .d.ts via addExtraLib. That file is not published
// anywhere, but it ships in the client bundle, so pull it straight from there.
// Every filename is content-hashed, hence the crawl instead of a fixed URL.
const ORIGIN = 'https://play.classicuo.org';
const OUTPUT = 'types/classicuo-scripting.d.ts';

const get = async (path) => {
  const response = await fetch(`${ORIGIN}${path}`);
  if (!response.ok) {
    throw new Error(`${path} -> HTTP ${response.status}`);
  }
  return response.text();
};

const index = await get('/');
const entry = index.match(/src="(\/index-[^"]+\.js)"/)?.[1];
if (!entry) {
  throw new Error('could not find the entry bundle in the page source');
}

const bundle = await get(entry);
const chunk = bundle.match(/"(\.\/scripting-dts-[^"]+\.js)"/)?.[1];
if (!chunk) {
  throw new Error('could not find the scripting-dts chunk - did addExtraLib change?');
}

const module = await get(`/${chunk.replace('./', '')}`);

// The chunk is a JS module whose default export is the whole .d.ts as one string literal
const literal = module.match(/scripting_d\s*=\s*('(?:[^'\\]|\\.)*')/)?.[1];
if (!literal) {
  throw new Error('could not find the d.ts string literal in the chunk');
}

const text = JSON.parse(
  `"${literal.slice(1, -1).replaceAll('\\\'', "'").replaceAll('"', '\\"')}"`,
);

writeFileSync(OUTPUT, text);
console.log(`wrote ${OUTPUT} (${text.length} chars, ${text.split('\n').length} lines)`);
console.log(`  entry: ${entry}`);
console.log(`  chunk: ${chunk}`);
