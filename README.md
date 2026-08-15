# ultima-online

Scripts for the ClassicUO web client, written as TypeScript modules and bundled into single
paste-ready files.

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
| `dist/sell.js` | Target items until you press ESC, sell every stack of them | [src/selling](src/selling/README.md) |
| `dist/sell-watch.js` | Target items until you press ESC, then sell them in batches as the pack fills | [src/selling](src/selling/README.md) |
| `dist/train.js` | Trains a skill by casting through a table of stages, meditating between them — Bushido out of the box | [src/training](src/training/README.md) |
| `dist/necro.js` | The same run for Necromancy: Pain Spike, the forms, and Wither, bandaging itself at a health floor | [src/necromancy](src/necromancy/README.md) |
| `dist/magery.js` | The same run for Magery, on the spells that gain without something to hit | [src/magery](src/magery/README.md) |
| `dist/chivalry.js` | The same run for Chivalry, which spends tithing points as well as mana | [src/chivalry](src/chivalry/README.md) |

## Why a build step

The client's script editor is one buffer with no module system, and the runtime is QuickJS — no
`import`, no `fetch`, no `localStorage`. Bundling is the only way to split code across files.

```bash
npm install
npm run build      # typecheck, then src/ -> the thirteen files in dist/
npm run watch      # rebuild on save
npm run typecheck  # tsc against the client's own typings, then again over the tests
npm test           # vitest, no client and no shard needed
npm run test:watch
```

Then paste the contents of one of the `dist/` files into the editor.

Output is IIFE-wrapped on purpose: the QuickJS context persists between runs, so a top-level `const`
collides with the previous run's and the client fails with *invalid redefinition of global
identifier*.

## Layout

```
src/lib/           everything more than one script does (see below)
src/boxes/         empty the crafted wooden boxes, keys on the floor (+ a key dump and a drop probe)
src/chivalry/      train Chivalry through its five bands, on the same loop as src/training/
src/lumberjacking/ chop the nearest tree, make boards, load the pack animals
src/magery/        train Magery on the spells that gain without a victim, on the same loop as src/training/
src/mining/        mine the nearest vein, smelt the ore on a fire beetle (+ a stand-still variant and an ore tile probe)
src/necromancy/    train Necromancy through its five bands, on the same loop as src/training/
src/selling/       sell-to-vendor: target items until ESC, sell every stack of them
src/training/      train a skill by casting the ability that still gains at the level it is at
types/             the client's TypeScript definitions (see below)
scripts/           type retrieval and patching
dist/              build output - this is what you paste
```

Tunables live in each folder's `config.ts` — item names, delays, how much to keep back. Some are
re-exported straight out of `src/lib/timings.ts`; the folder is still the only file anything
imports, and giving one its own value means deleting it from the re-export list and declaring it
below.

`src/lib/` holds what more than one script does, parameterised so the folder keeps its own wordings
and its own state:

```
arts        graphics two scripts would otherwise disagree about
cast        one cast, and what the shard made of it
clock       one Date.now(), so tests have one thing to fake
containers  container detection, opening, and depth-first search
convert     resource -> product, judged by pack diff, with per-hue write-off
die         exit() that the compiler will narrow on
entity      hex, Chebyshev distance, item-vs-mobile, name-or-serial, walk-to-a-mobile
guards      the stop conditions, composed per folder
heal        bandaging the character, proved by the health going up
heartbeat   'still here', on the clock rather than per cycle
loop        the idle wait, the stall watchdog, the throttle backoff
meditate    getting the mana back, with or without hands to clear first
outcomes    a journal phrase table and the reverse lookup off it
pack        counting and diffing what the backpack holds
retry       issue, poll for the proof, reissue
save        sitting out a world save
skill       every read of getSkill, and what a client that has not answered means
stages      the skill-stage table, and which band a value falls in
store       state parked on globalThis so it outlives the run
tiles       the tile cooldown map and the terrain scan
timings     the constants both harvest scripts agreed on
tool        find it, learn its graphic, equip it, notice it break
trainer     the training loop both trainers run
vendor      sell gumps
vitals      the one place player.maxMana and player.maxHits are read
walk        one naive step, optionally inside a box
gear        taking the kit off for a trance and putting the same pieces back, by serial
weapon      drawing what is in hand by graphic - gear's fallback, and the noWeapon recovery
weight      the one place player.weightMax is read
```

Nothing in `src/lib/` imports a folder's `config.ts`; the parameters come in through the call. The
modules that hold state are factories rather than singletons — two scripts in one test process must
not share a latch.

## Tests

`npm test` runs the suite against a fake client, so it needs neither the game nor a shard.

`src/test-support/uo.ts` is the fake world: `installGlobals()` puts stand-ins for `player`,
`client`, `target`, `journal`, the enums and `log`/`sleep`/`exit` on `globalThis`, and `item()` /
`mobile()` / `tile()` build fixtures. `sleep` is a no-op, which is why the poll loops finish in
milliseconds. Globals are assigned rather than stubbed because `walk.ts` reads them *while being
evaluated*, before any test body runs.

A test belongs in the shared module if that is where the logic is. `src/lib/walk.test.ts` covers the
stepping; `lumberjacking/walk.test.ts` covers only what the folder decides — that it passes
`allowedStep` and slides along the box edge, where mining passes no constraint at all.

Three things to know before adding tests:

- **Modules keep state between tests.** `tree.ts` memoizes tiledata lookups, the converters count
  misses per hue, and the tools latch the graphic they learned. Those tests call `vi.resetModules()`
  and then `await import(...)`. A shared factory can also just be called again for a fresh one.
- **`vi.resetModules()` does not clear `globalThis`,** and `memory.ts` is on `globalThis` on
  purpose. `tree.test.ts` calls `forget()` from a freshly imported `memory.js` *before* importing
  `tree.js`, or each test inherits the last one's blocked tiles.
- **A config read at module scope needs `vi.doMock('./config.js', ...)`,** not an assignment.
  `bounds.ts` and everything downstream of it read `BOUNDS` that way. Most such tests mock `BOUNDS`
  to `undefined`, since the checked-in box would hide every fixture.

The scripts are type-checked with no `@types/node` and no DOM lib, because QuickJS has neither —
`tsconfig.json` excludes the tests and `tsconfig.test.json` checks those separately. `npm run
typecheck` runs both; `npm run build` only checks what actually gets pasted.

## Types

`src/` is TypeScript under `strict: true`, checked against the client's own typings. esbuild strips
types without checking them, so `npm run build` runs `tsc --noEmit` first; `npm run watch` skips the
check to stay fast. The client's API types (`Item`, `Mobile`, `Gump`, `player`, `client` and the
rest) are ambient globals, so nothing imports them.

`npm run types` pulls the real `.d.ts` out of the running web client and patches it.
`scripts/fetch-types.mjs` crawls `play.classicuo.org` for the content-hashed `scripting-dts-*.js`
chunk and extracts the string literal — filenames change on every client release, which is why it
crawls rather than hardcoding a URL.

That file is not valid standalone TypeScript. Monaco tolerates the breakage, `tsc` does not, so
`scripts/patch-types.mjs` rewrites it into `types/classicuo.d.ts`:

- `declare module enums` is emitted as a bare identifier where a module name belongs
- the enums module re-exports itself ten times
- `declare module globalThis` collides with the built-in, so the globals are re-emitted as plain
  ambient declarations
- `VendorItem`, `TargetInfo` and `MenuPopupData` are referenced but never defined — stubbed as
  `any`, since their real shape is not shipped

`types/classicuo-scripting.d.ts` is the pristine download; `types/classicuo.d.ts` is generated —
edit the patch script, not the output.

## Notes that apply everywhere

Written against UOAlive. What is specific to one script lives in that folder's README; these are the
ones that bit more than one of them.

- **`player.weightMax` reads 0 while the client is refreshing stats**, against which every weight in
  the game is over the limit. A live run ended at *overweight (436/453)* on exactly that. Every read
  goes through `src/lib/weight.ts`. **`player.maxMana` and `player.maxHits` have the same fault**,
  and it is worse where something waits on one: a mana ceiling of 0 makes "wait until the pool is
  full" true the instant it is asked, so a trainer casts with no mana forever. Read through
  `src/lib/vitals.ts`.
- **Reading `contents` can throw, not just come back undefined.** A live run died on
  `Exception executing 'itemGetContents': Unexpected end of JSON input` mid-smelt. Every read goes
  through `contentsOf` / `packContents` in `src/lib/containers.ts`, which treat a throw as the
  `undefined` an unopened container already reports.
- **A container's `contents` is `undefined` until it has been opened.** That is why the mining script
  opens containers before concluding it has no spare pickaxe, and why the box and hoist searches open
  one level deeper per pass.
- **`player.use()` on a non-container *uses* it** — on a potion, that means drinking it. Only items
  positively identified as containers are opened; extend `CONTAINER_GRAPHICS` in
  `src/lib/containers.ts` if a bag is missed.
- **Item names are empty until the client has tooltip data**, so matching prefers graphics and falls
  back to names. An art learned through the name route is remembered.
- **A world save is a pause, not a fault, and it used to end the run.** The shard stops answering for
  several seconds, and every cycle of it reads as an unreadable outcome — five in a row is the stop
  condition. It has its own `OUTCOME_TEXT` bucket now, and the loop sits it out (`save.ts`).
- **What a save costs is not one wasted cycle, it is a wrong thing remembered.** Every silent
  operation concludes something from silence, and a frozen server is silent in exactly the way a real
  refusal is: the smelt writes a hue off as unworkable, `makeBoards` does the same to a wood, and the
  haul reads *weight did not move* as an animal that will take no more. So `SAVING_TEXT` is named
  separately from the outcome bucket, and each of those checks it first.
- **"You must wait" was the one branch that could spin forever in silence.** A fixed 600ms retry is
  shorter than the harvest delay on most shards, so the refused swing re-armed the very timer it was
  waiting out. It now counts (`MAX_THROTTLED`) and backs off further each time, capped at 8s, which
  self-tunes since a landed swing resets the counter. `OUTCOME_TEXT.throttled` lists the full
  wordings first, with the bare `You must wait` prefix kept last as a fallback.
- **A progress line counted with `tally % LOG_EVERY === 0` reprints itself.** That is a property of
  the count, not of the cycle. Both loops compare against the tally at the last line instead.
- **A loop that goes quiet is indistinguishable from a hung one**, so `heartbeat.ts` logs *still
  here* every `HEARTBEAT_EVERY` whatever branch the loop took — on the clock rather than per cycle,
  since a cycle is 300ms or 8s depending on which waits it hit. `STALL_WARN`/`STALL_STOP` end a run
  that has stopped getting anywhere. Waiting for a resource to come back counts against neither.
- **Which guards apply is a property of what the script does to the pack.** A harvest script fills it
  and `src/boxes/` empties it onto the floor, so the same overweight check that protects one stops
  the other on exactly the character it would have relieved. `src/lib/guards.ts` is composed per
  folder for that reason.
- **Serials come back as signed 32-bit ints**, so one prints as `0x-3266af2f` unless run through
  `>>> 0`. `hex()` in `src/lib/entity.ts` does the shift.
