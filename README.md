# ultima-online

Scripts for the ClassicUO web client, written as TypeScript modules and bundled into
single paste-ready files.

## The scripts

Each folder has its own README covering what its scripts do, what has to be true before you paste
one, and what to set. Start there.

| Script | What it does | README |
| --- | --- | --- |
| `dist/mining.js` | Mines the nearest vein and smelts the ore on a fire beetle | [src/mining](src/mining/README.md) |
| `dist/mine-here.js` | Mines the spot you are standing on until it runs dry, without moving at all | [src/mining](src/mining/README.md) |
| `dist/mine-probe.js` | Read-only: lists the land arts around you, to calibrate `ORE_TILE_GRAPHICS` | [src/mining](src/mining/README.md) |
| `dist/lumberjack.js` | Chops the nearest tree, makes boards, loads the pack animals | [src/lumberjacking](src/lumberjacking/README.md) |
| `dist/boxes.js` | Empties crafted wooden boxes, keys on the floor, optionally sells the boxes | [src/boxes](src/boxes/README.md) |
| `dist/keys.js` | Drops the keys already in your pack | [src/boxes](src/boxes/README.md) |
| `dist/key-probe.js` | Works out which client call actually puts an item on the ground here | [src/boxes](src/boxes/README.md) |
| `dist/sell.js` | Target an item, sell every stack of it | [src/selling](src/selling/README.md) |
| `dist/sell-watch.js` | Target an item, then sell it in batches as the pack fills | [src/selling](src/selling/README.md) |
| `dist/train.js` | Trains a skill by casting through a table of stages, meditating between them — Bushido out of the box | [src/training](src/training/README.md) |

## Why a build step

The client's script editor is one buffer with no module system — no `import`, no
`require`, no file management. The runtime is QuickJS, so there is no `fetch` and no
`localStorage` either; nothing can reach outside the editor at runtime. Bundling is the
only way to split code across files.

```bash
npm install
npm run build      # typecheck, then src/ -> the ten files in dist/
npm run watch      # rebuild on save
npm run typecheck  # tsc against the client's own typings, then again over the tests
npm test           # vitest, no client and no shard needed
npm run test:watch
```

Then paste the contents of one of the `dist/` files into the editor.

Output is IIFE-wrapped on purpose. The QuickJS context persists between runs, so a
top-level `const` collides with the previous run's and the client fails with
*invalid redefinition of global identifier*. Nothing inside an IIFE is ever global.

## Layout

```
src/lib/           everything more than one script does (see below)
src/boxes/         empty the crafted wooden boxes, keys on the floor (+ a key dump and a drop probe)
src/lumberjacking/ chop the nearest tree, make boards, load the pack animals
src/mining/        mine the nearest vein, smelt the ore on a fire beetle (+ a stand-still variant and an ore tile probe)
src/selling/       sell-to-vendor: target an item, sell every stack of it
src/training/      train a skill by casting the ability that still gains at the level it is at
types/             the client's TypeScript definitions (see below)
scripts/           type retrieval and patching
dist/              build output - this is what you paste
```

Tunables live in each folder's `config.ts` — item names, delays, how much to keep back. Some of
those are re-exported straight out of `src/lib/timings.ts`, which is where a value both harvest
scripts agreed on lives; the folder is still the only file anything imports, and giving one its own
value means deleting it from the re-export list and declaring it below.

`src/lib/` holds what more than one script does, parameterised so the folder keeps its own wordings
and its own state:

```
arts        graphics two scripts would otherwise disagree about
clock       one Date.now(), so tests have one thing to fake
containers  container detection, opening, and depth-first search
convert     resource -> product, judged by pack diff, with per-hue write-off
die         exit() that the compiler will narrow on
entity      hex, Chebyshev distance, item-vs-mobile, name-or-serial, walk-to-a-mobile
guards      the stop conditions, composed per folder
heartbeat   'still here', on the clock rather than per cycle
loop        the idle wait, the stall watchdog, the throttle backoff
outcomes    a journal phrase table and the reverse lookup off it
pack        counting and diffing what the backpack holds
retry       issue, poll for the proof, reissue
save        sitting out a world save
stages      the skill-stage table, and which band a value falls in
store       state parked on globalThis so it outlives the run
tiles       the tile cooldown map and the terrain scan
timings     the constants both harvest scripts agreed on
tool        find it, learn its graphic, equip it, notice it break
vendor      sell gumps
vitals      the one place player.maxMana is read
walk        one naive step, optionally inside a box
weight      the one place player.weightMax is read
```

Nothing in `src/lib/` imports a folder's `config.ts`; the parameters come in through the call. The
modules that hold state are factories rather than singletons for that reason — two scripts in one
test process must not share a latch.

## Tests

`npm test` runs the suite against a fake client, so it needs neither the game nor a shard.
Vitest rather than Jest because it transforms TypeScript and ESM through esbuild — the same
transform `build.mjs` already uses — so the `.js`-extension imports work with no config.

`src/test-support/uo.ts` is the fake world: `installGlobals()` puts stand-ins for `player`,
`client`, `target`, `journal`, the enums and `log`/`sleep`/`exit` on `globalThis`, and `item()`
/ `mobile()` / `tile()` build fixtures. `sleep` is a no-op, which is why the poll loops finish
in milliseconds. Globals are assigned rather than stubbed because `walk.ts` reads them *while being
evaluated*, before any test body runs.

Where a test belongs: the shared module, if that is where the logic is. `src/lib/walk.test.ts`
covers the stepping, and `lumberjacking/walk.test.ts` covers only the thing the folder decides —
that it passes `allowedStep` and slides along the box edge, where mining passes no constraint at
all. Before the extraction those two files were one test suite and one untested copy of it.

Three things to know before adding tests:

- **Modules keep state between tests.** `tree.ts` memoizes tiledata lookups, the converters count
  misses per hue, and the tools latch the graphic they learned. Those tests call `vi.resetModules()`
  and then `await import(...)`. A shared factory can also just be called again for a fresh one,
  which is why `lib/heartbeat.test.ts` needs no module reset.
- **`vi.resetModules()` does not clear `globalThis`,** and `memory.ts` is on `globalThis` on
  purpose. `tree.test.ts` calls `forget()` from a freshly imported `memory.js` *before* importing
  `tree.js`, or each test inherits the last one's blocked tiles. That same non-clearing is what the
  restart tests use to prove the store survives a run.
- **A config read at module scope needs `vi.doMock('./config.js', ...)`,** not an assignment.
  `bounds.ts` and everything downstream of it read `BOUNDS` that way. Most such tests mock
  `BOUNDS` to `undefined`: the checked-in box is a specific spot on the shard and `nearestTree`
  filters everything outside it, so the real one would hide every fixture.

The scripts are type-checked with no `@types/node` and no DOM lib, because QuickJS has neither —
`tsconfig.json` therefore excludes the tests, and `tsconfig.test.json` checks those separately
with the node types they need. `npm run typecheck` runs both; `npm run build` only checks what
actually gets pasted.

What the suite is for is pinning the decisions in each folder's *Notes on the shard*, most of which
were expensive to learn: the pack-diff key carrying hue as well as graphic, `isContainer` refusing to
guess (`player.use()` on a potion drinks it), giving up on a wood only after `CONVERT_ATTEMPTS`
silent tries rather than one, `allowedStep` sliding along the box edge instead of giving up, a lone
ore being skipped by size rather than written off by hue, and `overweight()` refusing to read a
`weightMax` of 0 as an overloaded character. It cannot check anything a shard has to answer.

## Types

`src/` is TypeScript under `strict: true`, checked against the client's own typings. esbuild
strips the types without checking them, so `npm run build` runs `tsc --noEmit` first — a type
error stops the build rather than reaching `dist/` and the game. `npm run watch` skips the check
to stay fast.

The client's API types (`Item`, `Mobile`, `Gump`, `player`, `client` and the rest) are ambient
globals, so nothing imports them.

`npm run types` pulls the real `.d.ts` out of the running web client and patches it.

The client feeds Monaco a `scripting.d.ts` via `addExtraLib`; it is not published
anywhere, but it ships inside the client bundle. `scripts/fetch-types.mjs` crawls
`play.classicuo.org` for the entry bundle, finds the content-hashed `scripting-dts-*.js`
chunk, and extracts the string literal — filenames change on every client release, which
is why it crawls rather than hardcoding a URL.

That file is not valid standalone TypeScript. Monaco tolerates the breakage, `tsc` does
not, so `scripts/patch-types.mjs` rewrites it into `types/classicuo.d.ts`:

- `declare module enums` is emitted as a bare identifier where a module name belongs
- the enums module re-exports itself ten times
- `declare module globalThis` collides with the built-in, so the globals are re-emitted
  as plain ambient declarations
- `VendorItem`, `TargetInfo` and `MenuPopupData` are referenced but never defined — they
  are stubbed as `any`, since their real shape is not shipped and is unknown

Both scripts are re-runnable. `types/classicuo-scripting.d.ts` is the pristine download;
`types/classicuo.d.ts` is generated — edit the patch script, not the output.

## Notes that apply everywhere

Written against UOAlive. What is specific to one script lives in that folder's README; these are the
ones that bit more than one of them.

- **`player.weightMax` reads 0 while the client is refreshing stats**, and every weight in the game
  is greater than zero, so an unguarded `weight > weightMax - buffer` reads a stat refresh as an
  overloaded character. A live run ended at *overweight (436/453)* on exactly that: the branch
  opened on a max of 0, the figure had recovered by the time anything read it again, and the stop
  printed a weight comfortably inside the limit it claimed to have exceeded. Every read of the limit
  goes through `src/lib/weight.ts`. **`player.maxMana` has the same fault** — the typings say so in as
  many words for `maxHits` — and it is worse where something waits on it: a mana ceiling of 0 makes
  "wait until the pool is full" true the instant it is asked, so a trainer meditates for no time at
  all and then casts with no mana, forever. That read goes through `src/lib/vitals.ts`.
- **Reading `contents` can throw, not just come back undefined.** A live run died on
  `Exception executing 'itemGetContents': Unexpected end of JSON input`, raised out of a pack count
  in the middle of a smelt — the client holding no data for a sub-bag and saying so with a truncated
  answer instead of an empty one. Nothing above it has a `try` in it, so an unreadable bag takes the
  whole run. Every read goes through `contentsOf` / `packContents` in `src/lib/containers.ts`, which
  treat a throw as the `undefined` an unopened container already reports, and say so once per serial
  rather than once per scan.
- **A container's `contents` is `undefined` until it has been opened.** That is why the mining script
  opens containers before concluding it has no spare pickaxe, and why the box and hoist searches open
  one level deeper per pass.
- **`player.use()` on a non-container *uses* it,** so only items positively identified as containers
  are ever opened — on a potion that means drinking it. Extend `CONTAINER_GRAPHICS` in
  `src/lib/containers.ts` if a bag is missed; the failure path logs the graphics it saw.
- Item names are empty until the client has tooltip data for them, so matching prefers graphics and
  falls back to names — and an art learned through the name route is remembered, so it costs one
  tooltip and then goes back to being a graphic lookup.
- **A world save is a pause, not a fault, and it used to end the run.** The shard stops answering
  for several seconds while it writes its world file: the swing is refused, the journal answers with
  none of the harvest wordings, and every cycle of it reads as an unreadable outcome — five in a row
  is the stop condition. It has its own `OUTCOME_TEXT` bucket in both harvest scripts now, and the
  loop sits it out (`save.ts`), sliced into `SAVE_POLL` sleeps and ended early by the completion
  line. Found on a mining run; lumberjacking had the identical gap.
- **What a save costs is not one wasted cycle, it is a wrong thing remembered.** Every silent
  operation in these scripts concludes something from silence, and a frozen server is silent in
  exactly the same way a real refusal is: the smelt writes a hue off as unworkable after three
  attempts, `makeBoards` does the same to a wood, and the haul reads *weight did not move* as an
  animal that will take no more and latches hauling off for the rest of the run. So `SAVING_TEXT` is
  named separately from the outcome bucket, and each of those checks it before drawing its
  conclusion — one unlucky ten seconds should not change how the next hour behaves.
- **"You must wait" was the one branch that could spin forever in silence.** It slept a fixed
  `STEP_DELAY * 2` (600ms) and swung again, which is shorter than the harvest delay on most shards
  — so the refused swing re-armed the very timer it was waiting out, standing still and logging
  nothing, bounded only by the 5000-cycle backstop. It now counts (`MAX_THROTTLED`) and backs off
  further each time (1s, 2s, 3s… capped at 8s), which both out-waits a real delay within a couple
  of swings and self-tunes to the shard's actual pacing, since a landed swing resets the counter.
  `OUTCOME_TEXT.throttled` also matched the bare prefix `You must wait`, which catches unrelated
  "you must wait N seconds" messages; the full wordings come first now, with the prefix kept last as
  a fallback.
- **A progress line counted with `tally % LOG_EVERY === 0` reprints itself.** That is a property of
  the count, not of the cycle, so it stays true for every cycle after the twenty-fifth chop until
  the next one lands — a run that then walks, waits or is refused says the same line over and over.
  Both loops compare against the tally at the last line instead.
- **A loop that goes quiet is indistinguishable from a hung one**, so `heartbeat.ts` logs *still
  here* with the phase, cycle, position and tally every `HEARTBEAT_EVERY` (30s) whatever branch the
  loop took — on the clock rather than per cycle, since a cycle is 300ms or 8s depending on which
  waits it hit. The respawn idle is the one path that skips it, because it already reports on its
  own cadence. Alongside it, `STALL_WARN`/`STALL_STOP` count cycles since the last swing landed and
  end the run at 300 rather than letting it reach `MAX_CYCLES`. Waiting for a resource to come back
  does not count against either.
- **`src/mining/` used to carry its own copies of `walk.ts`, `guards.ts`, `heartbeat.ts`,
  `memory.ts` and most of the rest, and the reasons given for it turned out to be reasons for
  separate *configuration and state*, not separate code.** Each folder is still one paste-ready
  script with its own `config.ts`, only one of them has a box, and the two memory stores are still
  keyed apart so one script's bans cannot hide the other's tiles — all of which the shared modules
  take as parameters. What the copies actually cost is that a lesson learned in one folder never
  reached the other: `player.weightMax` reading 0 mid-refresh killed a mining run and was guarded
  there, while the same unguarded expression sat in lumberjacking's guards, its haul trigger, its
  haul fallback, and in boxes' guards, where it would have stopped a run on cycle zero. Sharing is
  what stops that happening a fourth time. Bundling is per entry, so it costs nothing in `dist/`
  beyond the parameterisation.
- **Which guards apply is a property of what the script does to the pack.** A harvest script fills
  it and `src/boxes/` empties it onto the floor, so the same overweight check that protects one
  stops the other on exactly the character it would have relieved. `src/lib/guards.ts` is composed
  per folder rather than shared whole for that reason.
- **Gump serials come back as signed 32-bit ints**, so one prints as `0x-3266af2f` unless run
  through `>>> 0`. `hex()` in `src/lib/entity.ts` does the shift.
