import * as esbuild from 'esbuild';

// Each entry becomes one paste-ready script in dist/
const ENTRIES = [
  { in: 'src/boxes/index.ts', out: 'boxes' },
  { in: 'src/boxes/keys.ts', out: 'keys' },
  { in: 'src/boxes/probe.ts', out: 'key-probe' },
  { in: 'src/lumberjacking/index.ts', out: 'lumberjack' },
  { in: 'src/mining/index.ts', out: 'mining' },
  { in: 'src/mining/probe.ts', out: 'mine-probe' },
  { in: 'src/selling/index.ts', out: 'sell' },
  { in: 'src/tinkering/index.ts', out: 'tinker' },
  { in: 'src/tinkering/probe.ts', out: 'tinker-probe' },
];

// iife matters: the QuickJS context persists between runs, so top-level declarations
// would collide with the previous run's ("invalid redefinition of global identifier")
const options = (entry) => ({
  entryPoints: [entry.in],
  outfile: `dist/${entry.out}.js`,
  bundle: true,
  format: 'iife',
  target: 'es2020',
  charset: 'utf8',
  legalComments: 'none',
});

const watch = process.argv.includes('--watch');

if (watch) {
  const contexts = await Promise.all(ENTRIES.map((entry) => esbuild.context(options(entry))));
  await Promise.all(contexts.map((context) => context.watch()));
  console.log('watching src/ ...');
} else {
  await Promise.all(ENTRIES.map((entry) => esbuild.build(options(entry))));
  console.log(`built ${ENTRIES.map((entry) => `dist/${entry.out}.js`).join(', ')}`);
}
