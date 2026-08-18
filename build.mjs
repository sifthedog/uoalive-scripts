import * as esbuild from 'esbuild';

const ENTRIES = [
  { in: 'src/boxes/index.ts', out: 'boxes' },
  { in: 'src/boxes/keys.ts', out: 'keys' },
  { in: 'src/chivalry/index.ts', out: 'chivalry' },
  { in: 'src/lumberjacking/index.ts', out: 'lumberjack' },
  { in: 'src/magery/index.ts', out: 'magery' },
  { in: 'src/mining/here.ts', out: 'mine-here' },
  { in: 'src/mining/index.ts', out: 'mining' },
  { in: 'src/necromancy/index.ts', out: 'necro' },
  { in: 'src/selling/index.ts', out: 'sell' },
  { in: 'src/selling/watch.ts', out: 'sell-watch' },
  { in: 'src/training/index.ts', out: 'train' },
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
