# ultima-online

Scripts for the ClassicUO web client, written as TypeScript modules and bundled into
single paste-ready files.

## Why a build step

The client's script editor is one buffer with no module system — no `import`, no
`require`, no file management. The runtime is QuickJS, so there is no `fetch` and no
`localStorage` either; nothing can reach outside the editor at runtime. Bundling is the
only way to split code across files.

```bash
npm install
npm run build      # typecheck, then src/ -> dist/boxes.js, dist/keys.js, dist/key-probe.js, dist/lumberjack.js, dist/mining.js, dist/mine-probe.js, dist/sell.js, dist/tinker.js, dist/tinker-probe.js
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
src/lib/          shared helpers (container detection and search, pack diffing, vendor gumps)
src/boxes/        empty the crafted wooden boxes, keys on the floor (+ a key dump and a drop probe)
src/lumberjacking/ chop the nearest tree, make boards, load the pack animals
src/mining/       mine the nearest vein, smelt the ore on a fire beetle (+ an ore tile probe)
src/selling/      sell-to-vendor: target an item, sell every stack of it
src/tinkering/    tinkering trainer: phase by skill, gump navigation, tool switching
types/            the client's TypeScript definitions (see below)
scripts/          type retrieval and patching
dist/             build output - this is what you paste
```

Tunables live in each folder's `config.ts` — item names, delays, how much to keep back.

## Tests

`npm test` runs the suite against a fake client, so it needs neither the game nor a shard.
Vitest rather than Jest because it transforms TypeScript and ESM through esbuild — the same
transform `build.mjs` already uses — so the `.js`-extension imports work with no config.

`src/test-support/uo.ts` is the fake world: `installGlobals()` puts stand-ins for `player`,
`client`, `target`, `journal`, the enums and `log`/`sleep`/`exit` on `globalThis`, and `item()`
/ `mobile()` / `tile()` build fixtures. `sleep` is a no-op, which is why the poll loops finish
in milliseconds. Globals are assigned rather than stubbed because `walk.ts` and `tinkering/gump.ts`
read them *while being evaluated*, before any test body runs.

Two things to know before adding tests:

- **Modules keep state between tests.** `tree.ts` memoizes tiledata lookups, `boards.ts` counts
  misses per hue, `axe.ts` / `pickaxe.ts` / `tool.ts` latch the graphic they learned. Those tests
  call `vi.resetModules()` and then `await import(...)`.
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

What the suite is for is pinning the decisions in *Notes on the shard* below, most of which were
expensive to learn: the pack-diff key carrying hue as well as graphic, `isContainer` refusing to
guess (`player.use()` on a potion drinks it), giving up on a wood only after `CONVERT_ATTEMPTS`
silent tries rather than one, `allowedStep` sliding along the box edge instead of giving up, and
skill phases reading `.base` so a +Tinkering ring cannot fake a finish. It cannot check anything
under *Known unverified* — those need a shard.

## Clearing a pack of tinkered boxes

`dist/boxes.js` finds every wooden box in the pack, opens it, throws the key on the floor at your
feet, and closes the windows again. Anything in a box that is *not* a key goes into the backpack
instead — that way round on purpose, so an art the script does not recognise ends up somewhere safe
rather than on the ground. `DROP_KEYS = false` in `src/boxes/config.ts` keeps the keys too, and
`DROP_SPREAD` moves where they land.

Before opening anything it reads each box's tooltip, because a container's OPL carries a
`Contents: 3/125, 4 stones` line and the count is enough to skip the ones that are already empty —
a query instead of a double-click, an `OPEN_DELAY` and a window. On a pile whose keys are mostly
out already that is the difference between opening a hundred boxes and opening two. `PEEK_CONTENTS`
turns it off. Note the tooltip gives a *count*, not a list: there is no way to know a box holds an
iron key specifically without opening it, and `undefined` always means "open it and see" rather
than "empty".

It does **not** sell the boxes. `SELL = true` turns that on, at which point it says `vendor sell`
and offers the emptied boxes to whoever is in earshot — stand next to a tinker or a carpenter if
you do. `LOG_EVERY_BOX` names each box and says where everything that came out of it went, which
is what puts the shard's real key graphic in the console.

`CLOSE_BOXES` decides how the windows shut. `'perBox'` is the default and closes each box's own
window as it is emptied, looking the gump up under the container's serial. `'allGumps'` calls
`client.closeAllGumps()` at the end — it definitely works, and it definitely also closes your
paperdoll, character sheet and journal, because the client has no per-container close.

### Clearing keys already in the pack

`dist/keys.js` takes the keys that are *already* in your backpack — the ones an earlier run put
there before dropping worked — and throws them at your feet. It touches nothing else. The search
recurses, so it also takes a key out of a bag or out of a box that is still holding one.

It reports every `LOG_EVERY_KEY` keys, because a pile of forty is otherwise one line, a long
silence, and one more line — which reads exactly like a hung script. It also gives up after
`MAX_STUCK` keys in a row refuse to drop, since each of those costs the full `DROP_TIMEOUT`.

### If the keys will not land on the floor

Paste `dist/key-probe.js`. It takes one key and tries eight shapes of drop on it — the documented
`moveItemOnGroundOffset` at two offsets, `moveItem` addressed to the ground's container serial with
and without coordinates, container `0`, the by-graphic twin, and moving the key into the pack first
in case the offset only works from somewhere the client tracks — reporting after each one where the
key actually is. The first one that gets it off you is the answer; pin it as `DROP_METHOD`.

It also prints the key's own `x`/`y`/`z` next to yours, which is the thing worth looking at: an
item's coordinates are documented as world ones, but for something in a container they are the slot
it occupies in that container's window. That is the likeliest reason an *offset* from where the key
"is" lands nowhere.

A box reported `unopened` is locked. It keeps its key, it is excluded from the sale, and the run
says how many there were.

**If the keys are not landing on the floor,** the closing line says which of the two reasons it
was: `0 of 0 keys on the floor` means nothing was recognised as a key, so put the graphic it
listed into `KEY_GRAPHICS`; `0 of 40` means they were recognised but no drop would land, and the
run will have said which calls it tried.

**If it says `0 wooden boxes` next to a pack full of them,** `BOX_GRAPHICS` is wrong for this
shard. The script tries the name as a fallback and prints the graphic it learned; failing that it
dumps the whole top level of the pack and stops. The graphic that repeats as often as you have
boxes is the one to paste into `BOX_GRAPHICS`.

## Tinkering needs calibrating first

A gump can only be poked, never read — `hasButton`, `containsText`, `reply`, `switchPage` and
nothing else. There is no way to enumerate a craft gump's buttons or read their labels, so the
lockpick and ring button IDs have to be found on the shard and pinned in config.

`PROBE_MODE` in `src/tinkering/config.ts` picks what the probe does:

- `'scan'` presses nothing. It dumps your pack, resolves the gump, and lists the buttons it
  finds — the safe first look.
- `'trial'` presses one button at a time and reports what each did to your pack. A button that
  adds a lockpick is the one you want. This is the only method that actually works here, because
  button existence and gump text both turn out to be unreliable (see below).
- `'outcome'` crafts exactly one lockpick and reports where the result text turned up.

Fill in `RECIPES` from what a trial run identifies, `npm run build`, then paste `dist/tinker.js`.
Until `RECIPES` is filled in it stops immediately and says so.

If the trainer logs *nothing observable happened*, the outcome strings are wrong for this shard:
set `PROBE_MODE = 'outcome'`, rebuild, and paste the probe once. That crafts exactly one lockpick
and reports where the result text turned up.

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

## Notes on the shard

Written against UOAlive.

- Ore piles come in four arts (`0x19B7`, `0x19BA`, `0x19B9`, `0x19B8`), which the stock tables
  call the 1, 2, 3 and 4+ stack sizes. **They are not that here** — a pile of 33 arrives wearing the
  one the tables call a single. So the arts are a set to match against and nothing more: ore is
  grouped by hue, never by graphic, and a stack's size is read from `item.amount` alone.
- Ore is consolidated by double-clicking one pile and targeting another, which is what
  works by hand there. A combine consumes one of the two piles, so the pack is rescanned
  between passes rather than planned up front.
- Item names are empty until the client has tooltip data for them, so matching prefers
  graphics and falls back to names.
- `target.query()` answers a click with `{serial, graphic, x, y, z, hue}`, and that return is
  the *only* place the clicked serial shows up: it does not move `target.lastSerial`, which
  still holds whatever was targeted before. Comparing `lastSerial` either side of a `query()`
  therefore reads a second run against the same item as a cancelled cursor — `src/selling/pick.ts`
  reads the serial off the return value for exactly this reason.
- A vendor's sell gump lists only the *top level* of your pack. Anything sitting in a bag
  inside it is not on offer and cannot be sold, however the request is phrased — the entry
  simply is not there to match. `src/selling/hoist.ts` moves matches out of bags first;
  `HOIST_FROM_BAGS = false` turns that off and sells only what is already loose.
- **`client.sendSellRequest` returns whether the packet went out, not whether the vendor took
  anything,** and a vendor that refuses does so in silence. The goods leaving the pack is the only
  proof a sale landed, so `waitForSale` in `src/lib/vendor.ts` polls the pack for the offered
  serials the same way `boxes/drop.ts` polls a drop. That is also what stopped both scripts saying
  `vendor sell` twice a run: the second gump used to exist only to find out whether the first pass
  had worked, and it costs speech and a 5s wait to answer a question the backpack answers for free.
  The gump is now reopened only when matching items are genuinely still loose in the pack, which is
  the case the multi-pass was written for — a pile too big for one gump to list.
- A container's `contents` is `undefined` until it has been opened. That is why the
  mining script opens containers before concluding it has no spare pickaxe.
- `player.use()` on a non-container *uses* it, so only items positively identified as
  containers are ever opened. Extend `CONTAINER_GRAPHICS` in `src/lib/containers.ts` if
  a bag is missed; the failure path logs the graphics it saw.
- Iron ingot stacks change graphic with size the same way ore piles do, so ingots are matched
  by a graphic set plus hue 0 rather than by one graphic.
- **A vendor will not buy a container that still holds something,** and a tinkered wooden box
  arrives with its key inside it. That is the whole reason `src/boxes/` exists: open every box,
  move its contents into the pack, and only then say `vendor sell`. A box is emptied *wholesale*
  rather than having its key picked out, so the script never has to identify a key correctly —
  `KEY_GRAPHICS` in its `config.ts` feeds one log line and nothing else.
- **Only a box watched going empty is ever offered.** A box whose `contents` is still `undefined`
  after the double-click never opened — locked, most likely — and it keeps its key. Once one has
  been skipped the sale switches from matching the gump by name to matching it by the serials the
  run emptied, and if none of them line up it stops rather than selling by name: the two numbering
  schemes disagreeing is exactly the case where a name match would hand over the box that would
  not open, key and all.
- Emptying a large pile would hit the 125-item container cap rather than the weight cap, because a
  key taken out of a box adds one item to the *top level* of the pack while the total weight is
  unchanged. Throwing the keys on the floor is what avoids that; `src/boxes/index.ts` still
  empties, sells and goes round again, because with `DROP_KEYS` off the cap is back.
- **`moveItemOnGroundOffset` offsets from *you*, not from the item, and 0/0/0 is your own tile.**
  `dist/key-probe.js` settled it: a key at container `0x4128e8bf`, x 79, y 79 became container
  `0xFFFFFFFF` at 3443, 2638, 32 — the tile the character was standing on. The doubt was worth
  having, because an item inside a container reports the *slot* it occupies as its x/y (79, 79
  above), so an offset from the item would have landed nowhere. It does not work that way.
- **A drop is polled for, not slept through, and this one cost a whole debugging round.** The call
  is silent and returns an undocumented number, so the only proof is the item's container changing.
  Read it back after a flat 700ms and a drop that had *worked* looked like one that had not —
  whereupon the recovery path moved the key "into the pack", which, since it was by then lying on
  the floor, picked it back up. Keys arriving in the main backpack were successful drops being
  undone. `DROP_TIMEOUT` / `DROP_POLL` replaced the flat sleep.
- **A container's tooltip says how much is in it, so most boxes never need opening.** RunUO renders
  `Contents: 3/125, 4 stones` into a container's OPL, which `src/boxes/peek.ts` reads the same way
  `tinkering/tool.ts` reads "uses remaining" — including the discipline of asking once and giving up
  on the property if the shard does not send it, rather than paying the OPL timeout per box forever.
  It is a count and not a list, so it can prove a box empty but never prove one holds a key.
- **UOAlive's wooden box is `0x09aa`,** not the `0x0e7d` of the stock art tables. It was identified
  at runtime off the name "Wooden Box", which is the whole reason the name fallback exists.
- **Guards copied from a crafting script are wrong in a script that empties things.** `boxes/` first
  inherited tinkering's dead / overweight / pack-full checks, and they stopped a live run before the
  first of fifteen boxes: emptying a box onto the floor *frees* weight and a pack slot, so the
  overloaded character those checks fire on is exactly who the run would have relieved. They now
  apply only when `DROP_KEYS` is off and the keys really do land in the pack.
- **A guard that stops a loop has to say so where it stops it.** The reason was being kept for a
  stop message that a `SELL = false` run never reached, so the console showed `15 wooden boxes` then
  `emptied 0` with nothing in between and no explanation for either.
- **What counts as a key decides what hits the floor, so it is matched two ways and fails safe.**
  `KEY_GRAPHICS` plus a `\bkey\b` test on the name — a whole word, because `key` inside `turkey`
  or `monkey` would put something on the ground that was never meant to go there. An art that
  matches neither goes into the pack, which is the harmless direction: a key you have to throw
  away by hand rather than a possession on the floor. The first key the client can name teaches
  the run its graphic, the way `tool.ts` latches the tinker's tools.
- Both harvest scripts have to find a specific tile: `src/lumberjacking/tree.ts` and
  `src/mining/vein.ts` scan `client.getTerrainList` around the player and pick the nearest
  candidate. The first hit is logged with its graphic and name either way.
- **`target.terrain` targets the *land* tile when the graphic argument is omitted, and the static
  standing on it when one is passed** — and the shard answers the land tile as mining rather than
  chopping. The chop therefore always passes the tree's graphic.
- **The dig names no tile at all: it answers the cursor with `waitTargetSelf` and lets the shard
  pick the ore.** That is what works by hand here, and it sidesteps every way an explicit
  `target.terrain` can be wrong — land versus static, and which of the several arts stacked on one
  tile is the one actually carrying ore. `vein.ts` still finds and books tiles, but its job is
  deciding where to *stand*: `MINE_RANGE` is the distance at which walking stops and swinging
  starts, not a range the shard enforces.
- **Trees can be identified by name and ore cannot.** `client.getStatic` reads the *static*
  tiledata, so `isTree` can ask the client whether an art is called a tree; a mountainside is a land
  tile, and `client.getTile` answers with flags and no name at all. `ORE_TILE_GRAPHICS` in
  `src/mining/config.ts` is therefore a graphic table rather than a name match, seeded with the
  stock RunUO mountain and cave bands. `dist/mine-probe.js` prints every distinct art around you
  with its `isLand` flag and tile count, which is what the table should actually be filled in from.
- **Land and static tiledata are numbered in separate tables**, so 1339 is a mountain band as land
  and a cave floor as a static. Everything in `vein.ts` that keys on an art keys on the kind too —
  the runtime ban is `land:231` rather than `231`, or one ban would hide an unrelated art.
- **A learned refusal has to outrank the seeded table.** `isTree` can afford to check its overrides
  first because `TREE_GRAPHICS` ships empty; `ORE_TILE_GRAPHICS` ships full, so asking it first made
  `markNotMineable` silently do nothing at all — the ban was recorded and then ignored on the very
  next scan. `isOre` asks the bans first and the seed second.
- **A fire beetle is a portable forge, and the smelt is the inverse of making boards.** Boards are
  the tool used and the resource targeted; smelting is the *ore* double-clicked and the *beetle*
  targeted. It is never double-clicked itself — it is rideable, so that mounts you.
- **Mining has to get off the mount first**, which is awkward precisely because the fire beetle is
  both the ride out and the smelter once you arrive. There is no dismount call in this API:
  `src/mining/mount.ts` double-clicks the player and polls `equippedItems.mount` until it clears.
- **Ore destroyed by a full pack is not ore dropped on the floor.** `packFull` has its own
  `OUTCOME_TEXT` bucket in mining, and it triggers a smelt rather than another swing; lumberjacking
  needs no equivalent, because logs stop it on weight long before the item cap.
- **Smelting is triggered by weight and nothing else** — `player.weight > player.weightMax`, once
  the shard has actually started refusing to move things. Not on a depleted vein (which says nothing
  about how full the pack is, and would mean walking to the beetle every time one ran dry), not at a
  buffer below the limit, and not as a finishing step. The corollary is that `guards.ts` has *no*
  weight check: one at the usual buffer below the limit would fire first, every time, and the smelt
  would never happen at all. What ends an overweight run is a smelt that freed nothing.
- **A full pack is answered by consolidating, not by smelting.** `packFull` means the container hit
  its item cap, so forty piles of one becoming one pile of forty is the fix that gives back
  thirty-nine slots; the ore that swing produced is destroyed rather than dropped, so it has to be
  answered before the next swing either way.
- **`item.amount` is 0 for a stack the client has no data for**, not 1 and not absent — so a size
  test written as `amount >= 2` skips *every* pile in the pack, and the run halts overweight beside
  a working beetle with ore it could have smelted. An unknown size is therefore worth one attempt,
  and only a size the client has actually reported as one is skipped. Reading the size off the art
  instead is not the way out: see the stack-size note above.
- **Ore is matched by graphic first and tooltip name second**, `\bore\b` as a whole word on the
  precedent of the key search in `src/boxes` — `ore` at the end of *sycamore* would put something in
  the smelter that was never meant to go there. An art learned that way joins `ORE_GRAPHICS`, so it
  costs one tooltip and then goes back to being a graphic lookup. It exists because the seeded arts
  come from the stack-size table this shard is already known to disagree with.
- **`player.weightMax` reads 0 while the client is refreshing stats**, and every weight in the game
  is greater than zero, so an unguarded `weight > weightMax` reads a stat refresh as an overloaded
  character. A live run ended at *overweight (436/453)* on exactly that: the branch opened on a max
  of 0, the figure had recovered by the time anything read it again, and the stop printed a weight
  comfortably inside the limit it claimed to have exceeded.
- **A condition is checked where it is decided, not again where it is acted on.** The same run
  smelted nothing at all, because the loop decided it was overweight and then called a helper that
  asked `tooHeavy()` a second time — by which point the answer had changed, so the smelt was skipped
  and the run stopped for being overweight without ever having tried. Two reads of a value the
  client updates asynchronously are two different values.
- **The proof that a smelt landed is ore leaving the pack, not weight going down.** `player.weight`
  can still be reporting its pre-smelt figure when the pack diff has already confirmed the
  conversion, and reading that as *smelting freed nothing* ended runs that were working fine.
- **A hue written off after three silent passes is a verdict worth reopening.** A beetle that
  stepped out of range, a run of throttled attempts and a stack that was briefly too small all look
  identical to an ore that cannot be worked. When the alternative is ending the run overweight,
  `retryUnsmeltable()` clears the write-offs for one more go; it returns false once there is nothing
  left to reconsider, which is what keeps that from looping.
- **Two ore make an ingot, so a stack of one cannot be smelted at all** — and the shard's refusal is
  silent, which in the pack diff is indistinguishable from a throttled attempt. Offered anyway, a
  lone ore burns `SMELT_ATTEMPTS` and then writes off the whole *hue*, taking every future stack of
  it along with it. `MIN_SMELT_AMOUNT` skips it by size instead, and remembers nothing: `groupOres`
  piles the hue together first, so whatever is still at one afterwards is genuinely the odd ore out,
  and the next swing that lands on that vein makes it two.
- **Mining has no bounds box, and the one it inherited stopped every run on cycle zero.** The folder
  was seeded with lumberjacking's forest rectangle, and `stopReason()` runs before the scan, the
  equip and the swing — so a character standing anywhere else exited immediately, having done
  literally nothing. Lumberjacking keeps its box because a forest is a place you work; mining roams,
  and what keeps a run somewhere sensible is where the ore is.
- **"There are no harvestable resources nearby" is about the area, not a tile** — the last word is
  the whole point, and it is the answer a swing that names no tile mostly gets. It has its own
  `OUTCOME_TEXT` bucket, and it parks every ore tile within `MINE_RANGE` on the respawn cooldown at
  once, which is what makes the character walk away. Before it had a bucket it read as an unreadable
  outcome: the character stood still, swung five times for the same sentence, and the run stopped.
  Parking only the vein the scan had picked would have done the same thing more slowly.
- **A run of empty spots is what a wrong `ORE_TILE_GRAPHICS` looks like from the outside.** The scan
  keeps finding ore because the table says the ground is ore; the shard keeps disagreeing. After
  `NOTHING_NEARBY_HINT` spots in a row the run says so once and lists the arts under the character's
  feet — those are the ones to correct.
- **A world save is a pause, not a fault, and it used to end the run.** The shard stops answering
  for several seconds while it writes its world file: the swing is refused, the journal answers with
  none of the harvest wordings, and every cycle of it reads as an unreadable outcome — five in a row
  is the stop condition. It has its own `OUTCOME_TEXT` bucket in both harvest scripts now, and the
  loop sits it out (`save.ts`), sliced into `SAVE_POLL` sleeps and ended early by the completion
  line. Found on a mining run; lumberjacking had the identical gap.
- **What a save costs is not one wasted cycle, it is a wrong thing remembered.** Every silent
  operation in these scripts concludes something from silence, and a frozen server is silent in
  exactly the same way a real refusal is: the smelt writes the hue off as unworkable after three
  attempts, `makeBoards` does the same to a wood, and the haul reads *weight did not move* as an
  animal that will take no more and latches hauling off for the rest of the run. So `SAVING_TEXT` is
  named separately from the outcome bucket, and each of those checks it before drawing its
  conclusion — one unlucky ten seconds should not change how the next hour behaves.
- **A dead end has to say what it saw.** `no ore in range` while standing on a mountain is the
  likeliest way a run ends on a shard whose tile numbering `ORE_TILE_GRAPHICS` does not match, and
  on its own it is unactionable, so the stop prints the commonest arts under your feet and marks
  which ones the config matches. `src/mining/survey.ts` is that listing, shared with the probe.
- `src/mining/` carries its own copies of `walk.ts`, `guards.ts`, `heartbeat.ts` and `memory.ts`
  rather than sharing lumberjacking's. That is deliberate, not an accident: each folder is one
  paste-ready script with its own `config.ts`, only one of them has a box at all, and the two memory
  stores are keyed apart so one script's bans cannot hide the other's tiles.
- One tree is several statics and only the trunk is harvestable, so a tile that runs out of wood
  is tracked per tile — a stump regrows, and a neighbour of the same art may still have wood.
- **A depleted tile is a cooldown, not a write-off.** The stump grows back, so *not enough wood*
  parks the tile until `REGROW_DELAY` (25 minutes) has passed and the scan picks it up again on its
  own. Written off permanently, the script bans every tile it ever chopped and stops with *no tree
  in range* while standing in a forest. When nothing in reach is choppable but something is coming
  back, the loop idles until the soonest one is due rather than ending the run — sliced into
  `IDLE_POLL` sleeps, because one blocking sleep of twenty minutes leaves the client unresponsive
  for all of them with no way to stop the script.
- **"Target cannot be seen." is line of sight, and permanent.** The tile is already inside
  `CHOP_RANGE`, so neither walking closer nor waiting changes the answer — something is simply in
  the way. It is written off for good. Before it had its own `OUTCOME_TEXT` bucket it read as an
  unreadable outcome, was picked again by the very next scan, and five in a row ended the run.
- **What the failures mean is now three different things, not one.** Out of wood → back in 25
  minutes. A walk that never closed → back in `UNREACHABLE_DELAY` (5 minutes), because what blocked
  the path is usually a player or a pet rather than the tree. Out of sight, out of shard-range, or
  an art that cannot be chopped → never again.
- **State that has to outlive the run lives on `globalThis`** (`src/lumberjacking/memory.ts`): the
  blocked tiles and the arts the shard refuses. The QuickJS context persists between runs — the
  same fact the IIFE wrapping exists for — so a restart of the script inherits them, though a
  restart of the client does not. A 25-minute cooldown is longer than most runs, so without this
  every restart would swing at the tiles that had just gone empty and re-learn the forest from
  scratch. The store carries a version and is discarded rather than read if it does not match, so
  an edit to its shape cannot crash the first scan after a rebuild. `NOT_TREE_GRAPHICS` in
  `config.ts` is therefore a seed only — runtime bans go to the store, not back into the config.
- **The tiledata name over-reaches.** A live run matched `0xc9e`, named *o'hii tree*, and the
  shard answered **"You can't use an axe on that"** — the art is scenery. That answer is about the
  *graphic*, not the tile, so a refusal adds the graphic to `NOT_TREE_GRAPHICS` at runtime and
  every other copy of that art drops out of the scan at once, rather than being walked to and
  refused one tile at a time across the whole forest. The console names each distinct graphic the
  scan settles on, so the art that does work ends up in the log next to the art that does not.
- **A loop that goes quiet is indistinguishable from a hung one**, so `heartbeat.ts` logs *still
  here* with the phase, cycle, position and tally every `HEARTBEAT_EVERY` (30s) whatever branch the
  loop took — on the clock rather than per cycle, since a cycle is 300ms or 8s depending on which
  waits it hit. The regrow idle is the one path that skips it, because it already reports on its
  own cadence. Alongside it, `STALL_WARN`/`STALL_STOP` count cycles since the last chop landed and
  end the run at 300 rather than letting it reach `MAX_CYCLES`. Waiting for wood to grow back does
  not count against either.
- **"You must wait" was the one branch that could spin forever in silence.** It slept a fixed
  `STEP_DELAY * 2` (600ms) and swung again, which is shorter than the harvest delay on most shards
  — so the refused swing re-armed the very timer it was waiting out, standing still and logging
  nothing, bounded only by the 5000-cycle backstop. It now counts (`MAX_THROTTLED`) and backs off
  further each time (1s, 2s, 3s… capped at 8s), which both out-waits a real delay within a couple
  of swings and self-tunes to the shard's actual pacing, since a landed chop resets the counter.
  `src/tinkering/index.ts` had the same branch and got the same fix. `OUTCOME_TEXT.throttled` also
  matched the bare prefix `You must wait`, which catches unrelated "you must wait N seconds"
  messages; the full wordings come first now, with the prefix kept last as a fallback.
- There is no pathfinding API — `player.walk`/`run` take one direction at a time. Walking to a
  tree is naive `Math.sign` stepping, and the direction is issued twice because the first packet
  in a new direction only turns the character. A tree that stops being reachable after
  `MAX_STEPS`, or that a step fails to close on at all, is written off like an exhausted one.
- `BOUNDS` in `config.ts` keeps the character inside a box, corners included. `stepToward` is the
  only thing that ever moves it, so that is the only place the box has to be enforced; `guards.ts`
  also stops the run if the character is outside one, which catches a teleporter, a boat, or a run
  started from the wrong place. A diagonal step that would leave the box falls back to whichever
  cardinal half stays inside, so the character slides along an edge instead of giving up — a box
  is mostly edge. Trees outside the box are still chopped when a legal standing tile is within
  `CHOP_RANGE` of them, and trees that no legal tile can reach are filtered out of the scan rather
  than picked, walked at, refused, and only written off `MAX_STEPS` later.
- Axes are two-handed and hatchets are one-handed, so the axe check reads
  `equippedItems.twoHanded ?? equippedItems.oneHanded` rather than mining's single hand layer.
- Logs become boards by using the axe and targeting the log stack — the same cursor the chop
  uses. Stock RunUO answers with a sound and no message, so the conversion is read from a pack
  diff (`src/lib/pack.ts`) rather than the journal. That diff also *names* the board graphic:
  whatever gained amount as the logs left is a board, so `BOARD_GRAPHICS` in `config.ts` is only
  a seed and a wrong guess corrects itself on the first conversion.
- Logs are matched by graphic alone, not graphic plus hue like ingots, because special woods are
  hued and still have to be counted and hauled.
- **A conversion is polled for, not slept through, and one silent attempt proves nothing.** The
  action throttle can hold a conversion past any pause worth taking, and a stale serial changes
  nothing either — both look exactly like a wood that cannot be worked. Reading the pack once
  after a fixed sleep and giving up on the hue there and then is what put ordinary logs on the
  pack animal: hue 0 is *every* normal log, so one hiccup disabled conversion for the whole run.
  `boards.ts` now polls for `CONVERT_TIMEOUT`, converts one stack per pass and rescans between
  them, and only gives up on a hue after `CONVERT_ATTEMPTS` silent tries in a row — or at once
  if the journal says outright that you are not skilled enough, which retrying cannot fix.
- Only boards and the logs of a given-up-on hue go onto the animal. A log still waiting its turn
  stays in the pack and the next haul retries it. The exception is a pack that is still over the
  haul threshold once the boards have gone: those logs travel as logs rather than ending the run
  overweight, and the haul logs a line saying so.
- Pack animals are found by body graphic within `SCAN_RADIUS`, keeping the ones whose
  `isRenamable` is true: only your own pets can be renamed, so that is what tells yours from a
  stranger's. Their packs come from `client.findItemOnLayer(serial, Layers.Backpack)`.
- **All of them get loaded, not just the nearest.** The haul walks the animals nearest-first and
  fills each in turn; one that stops accepting is full rather than broken, so what is left goes to
  the next. The leftover-logs fallback is asked only once every animal has had its turn — asking
  per animal would read a full first horse as the conversion having fallen behind, and would then
  try to push logs onto that same full horse.
- **Do not double-click the animal to find its pack if you can avoid it.** A giant beetle is
  rideable, so the double-click mounts you instead. `haul.ts` only falls back to it when the
  backpack layer comes back empty.
- Hauling fires at `HAUL_BUFFER` (120 stones of headroom), which is deliberately wider than the
  guards' `WEIGHT_BUFFER` (40), so there is room to work before the overweight stop. A haul that
  frees no weight latches hauling off for the rest of the run, or a missing animal would cost a
  fresh search every cycle.
- The tinkering menu is the ServUO craft gump: a category column (LAST TEN, Jewelry, Wooden
  Items, Tools, Parts, Utensils, Miscellaneous, Assemblies, Traps, Magic Jewelry), a ten-row
  selections pane with a NEXT PAGE button, and a bottom row of REPAIR / MARK / ENHANCE / ALTER /
  NON QUEST ITEM / MAKE LAST. **Its button numbering is still unknown.** The IDs `hasButton`
  reports fit `1 + kind + 20 * row`, but pressing what that implies landed on unrelated entries,
  so the pattern was fitted to noise. Deriving IDs arithmetically does not work here.
- **`Gump.last` returns null while the gump is still open.** `Gump.exists(serial)` keeps
  reporting it correctly, so `GUMP_SERIAL` is pinned and `craftGump()` looks the gump up by
  serial first, with `Gump.last` only as a fallback.
- Gump serials come back as signed 32-bit ints, so `Gump.lastSerial` prints as `0x-3266af2f`
  unless run through `>>> 0`. The tinkering gump is `0xcd9950d1`, and it is the same value
  across sessions, so it is a type id rather than a per-instance one.
- **`hasButton` over-reports.** It claims 26 groups of buttons where the window shows about
  forty clickable things, so a button existing is no evidence it is real. Navigation cannot be
  verified by button presence; press the button and check what changed in the pack instead.
- `switchPage` closes the gump rather than paging it, so it is not how this menu navigates.
- `containsText` does resolve cliloc text, but it matches against the whole gump — every
  category name and every item name hits on the page as opened — so it cannot identify a page.
  It is also a plain substring match, so `ring` matches `springs` and `earrings`.
- Stock RunUO renders craft results *inside the reopened craft gump* rather than sending a
  system message, so the journal may stay silent. `src/tinkering/craft.ts` falls back to
  diffing the ingot total and the tool's existence.
- `item.hits`/`maxHits` are 0 for items the client knows nothing about, which is the normal
  case in a pack, and a RunUO tool tracks `UsesRemaining` rather than hits anyway. Tool wear is
  detected by the serial no longer resolving through `client.findObject`.
- Skill phases key off `getSkill().base`, not `.value`, so +Tinkering jewelry cannot fake a
  finish or look like a skill drop when it falls off.

## Known unverified

- Whether the shard caps items per tile. `DROP_SPREAD` walks a key round the nine tiles under and
  around you rather than betting on one square, because the cost of being wrong is `DROP_TIMEOUT`
  per refused key — a minute of apparent silence over a pile of forty. Untested either way.
- Everything about lumberjacking, which has not been run yet. `client.getTerrainList` and
  `client.getStatic` are used for the first time here, the harvest phrasing in `OUTCOME_TEXT`
  is the stock RunUO wording as a hypothesis, and `LOG_GRAPHICS` assumes log stacks change
  graphic with size the way ore does. Wrong phrasing shows up as `unknown` outcomes, which stop
  the run after `MAX_UNKNOWN` rather than flailing; the pack log count is the silent fallback.
  Two phrases are now confirmed from live runs — `notTree` and `notSeen` — and the rest are still
  guesses.
- `REGROW_DELAY`. 25 minutes is a guess at the shard's respawn timer, on the same footing the
  `OUTCOME_TEXT` phrases were. If the script comes back to a tile that is still bare, that constant
  is the one to raise; the console names every tile it parks and when it expects it back.
- The pack animal bodies in `PACK_ANIMAL_GRAPHICS` (`0x123` pack horse, `0x124` pack llama,
  `0x317` giant beetle) and whether `Layers.Backpack` resolves for someone else's mobile at all.
  The search logs how many animals it found and their names; `PACK_ANIMAL_SERIALS` pins an exact
  list if the guesses are wrong.
- Whether boards actually weigh less than logs here. If they do not, converting frees nothing and
  only the animals make a difference to how long a run lasts.
- Whether the shard merges ore piles of differing graphics. `groupOres` logs and bails
  rather than looping if a combine makes no progress.
- **`ORE_TILE_GRAPHICS`**, which is the one that matters for mining. The bands are copied from the
  stock RunUO mountain and cave tables and nothing has confirmed them against UOAlive. Run
  `dist/mine-probe.js` standing on the face you mean to work: it never swings, targets or moves, it
  only lists the arts around you and marks the ones the config currently matches.
- The mining `OUTCOME_TEXT`, on the same footing as lumberjacking's — stock RunUO phrasing as a
  hypothesis. `empty` is the one that matters most: it is what parks a vein for `RESPAWN_DELAY`, so
  a wrong phrase there means the script keeps swinging at a worked-out tile until the unknown-outcome
  count stops the run.
- `RESPAWN_DELAY`. 25 minutes, chosen to match lumberjacking's `REGROW_DELAY` and not measured. If
  the script comes back to a vein that is still empty, that is the constant to raise; the console
  names every tile it parks and when it expects it back.
- The fire beetle body in `FIRE_BEETLE_GRAPHICS` (`0xa9`). The search logs the name and body of
  whatever it settles on, and `FIRE_BEETLE_SERIAL` pins one exactly if the guess is wrong.
- Whether a fire beetle actually smelts by being targeted with an ore stack on this shard, and
  whether it has to be yours. `isRenamable` is what tells your pet from a stranger's, the same trick
  the haul uses, and the smelt falls back to any beetle in range if none of them read as yours.
- Whether double-clicking yourself is how this shard dismounts. If it is not, `mount.ts` reissues
  three times and then stops the run saying so, rather than mining on regardless.
- Whether any craft outcome reaches the journal on UOAlive, and in what words. `OUTCOME_TEXT`
  in `src/tinkering/config.ts` holds the stock RunUO strings as a hypothesis;
  `PROBE_MODE = 'outcome'` settles it.
- Whether `Gump.containsText` resolves localized (cliloc) gump text. If the probe reports no
  keyword hits it does not, and craft navigation is positional with no text safety net.
- The tinker's tools graphics in `TOOL_GRAPHICS`. The probe logs the graphic of the tool it
  actually found.
- The tinkering resource sub-type. Nothing sets it, so crafts inherit whatever ingot type the
  character last picked in that menu — one who last worked dull copper will spend dull copper,
  which the iron-only ingot count cannot see.
- Whether lockpicks still grant gains all the way to 95.0 here. On stock difficulty tables they
  top out nearer 70, so a third recipe may be needed between the two phases.
