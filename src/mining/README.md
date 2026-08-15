# mining — dig ore, smelt it on a fire beetle

Builds three scripts:

| Script | What it does |
| --- | --- |
| `dist/mining.js` | Walks to the nearest vein, swings, consolidates the ore, and smelts it against a fire beetle |
| `dist/mine-here.js` | Stands still and works the spot you are on until it runs dry, then smelts and stops |
| `dist/mine-probe.js` | Read-only. Lists every land and static art around you, so `ORE_TILE_GRAPHICS` can be filled in |

**Run the probe first.** `ORE_TILE_GRAPHICS` ships as a stock RunUO guess and it is the one setting
most likely to be wrong for your shard. Everything else degrades gracefully; this one ends runs — for
`dist/mining.js`, at least. `dist/mine-here.js` never reads it, so if you only want to work the vein
you are standing on, the calibration is not in your way.

## Why it exists

Mining by hand is a swing, a wait, a look at the pack, a walk, and then the same thing again. The
interesting part is what to do with the ore: a full pack of it is twelve stones a piece, and getting
it to a forge means walking back to town.

A **fire beetle** is a portable forge. It is a pet, it follows you, and an ore stack double-clicked
and targeted at one comes back as ingots, which weigh almost nothing. That is why this script never
looks for a forge and never walks to town — and it is also why it has to get off the mount first,
since the beetle is usually both the ride out and the smelter once you arrive.

Unlike lumberjacking there is **no bounds box**. Mining roams; what keeps a run somewhere sensible
is where the ore is.

## What `dist/mining.js` does

Every cycle:

1. **Check the stop conditions** — dead, or the pack at its item cap.
2. **Get off the mount.** Asked every cycle, not once at the start, so a remount costs one cycle
   rather than the rest of the run. There is no dismount call in this API: it double-clicks the
   player and polls `equippedItems.mount` until it clears.
3. **Equip a pickaxe.** Also every cycle, so a broken tool costs one cycle. Spares are found in the
   pack, one level of bags down.
4. **The weight backstop.** If the pack is genuinely over the limit, smelt now. This is a backstop,
   not the plan — see below.
5. **Scan for a vein** within `SCAN_RADIUS`, nearest first, skipping tiles the run has parked.
6. **Walk to it** if it is further than `MINE_RANGE`. One naive `Math.sign` step per cycle; there is
   no pathfinding API. A vein that takes more than `MAX_STEPS` or that a step cannot close on is
   marked unreachable for `UNREACHABLE_DELAY`.
7. **Swing**, and branch on what the shard says.

The outcome branches:

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per hue |
| `empty` | Park that tile for `RESPAWN_DELAY`, **and smelt** — the spot has run dry |
| `nothingNearby` | Park *everything* within `MINE_RANGE`, so the next scan has to look further and the character walks off. **And smelt** |
| `notOre` | Ban the whole graphic, not just the tile — a wrong band in `ORE_TILE_GRAPHICS` is a whole stretch of mountain |
| `tooFar` | The shard disagreeing about the range. Set the tile aside rather than swinging again |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `packFull` | Consolidate. The pack is at its item cap, so forty piles of one becoming one pile of forty gives back thirty-nine slots |
| `wornOut` | The pickaxe broke; the next cycle equips a spare |
| `saving` | The shard is writing its world file. Sit it out; nothing is learned and no counter is held against it |
| `throttled` | Back off further each time (1s, 2s, 3s… capped), and give up after `MAX_THROTTLED` |
| `noCursor` | The shard declined to start the swing. Backed off like a throttle, but counted |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

**When it smelts:** on a spot running dry, not on a schedule and not at the end. The swings that
filled the pack are over, the character is about to walk somewhere else anyway, and the beetle has
been following it the whole time — so that is the cheapest moment in the run to convert. It costs
nothing on the passes with nothing to do, because `smeltAll` asks whether any pile is worth smelting
*before* it so much as looks for the beetle.

### Before you paste it

- Stand on the mountain face or in the cave you mean to work.
- **A pickaxe in hand.** The run learns its graphic from what you are holding. Spares go in the pack
  or in one bag inside it — `SPARE_BAG_SERIAL` pins a bag that is nested deeper than that.
- **The fire beetle nearby**, and yours. Without one the run still mines; it just stops when the
  pack fills, saying smelting freed nothing.
- Being mounted is fine — it gets off by itself.

### How to run it

```bash
npm run build
```

Paste `dist/mine-probe.js` first and correct `ORE_TILE_GRAPHICS`, rebuild, then paste
`dist/mining.js`. The first thing the run prints is the world as it sees it — mounted or not, what
is in your hand, your weight — because a run that stops on its first cycle otherwise looks exactly
like a script that never started.

## What `dist/mine-probe.js` does

It never swings, never targets and never moves. It walks the tiles within `PROBE_RADIUS` of you,
collects every distinct art, and prints each one with its `isLand` flag, its tiledata flags, how
many tiles carry it, and whether `ORE_TILE_GRAPHICS` currently matches it — commonest first, because
a mountain face is hundreds of tiles of the same handful of arts.

Graphics are printed in decimal as well as hex, since the RunUO tables the config is seeded from are
written in decimal.

The same listing is printed by the main loop when it ends with `no ore in range`, capped at
`SURVEY_ARTS` entries.

## What `dist/mine-here.js` does

The stationary half of `dist/mining.js`. It stands where you put it, swings until the shard says
there is nothing left, smelts what it mined, and stops.

It can leave out the scan, the walk, the block map and the respawn wait because of how the swing
works here: [`dig.ts`](dig.ts) answers the target cursor with *yourself* and lets the shard pick the
ore, so a swing is aimed by where the character is standing rather than by naming a tile. Everything
in [`vein.ts`](vein.ts) exists to decide where that is. Stand somewhere worth standing and none of it
has anything left to do — which is also why it does not matter which tile of the vein you are facing.

Every cycle: the same stop conditions, the same dismount, the same equip, the same weight backstop,
then a swing.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per hue |
| `empty`, `nothingNearby` | **The spot is worked out.** Consolidate, smelt, and stop. One branch, not two — the pair differ by scope, and scope only matters to a run that has somewhere else to walk |
| `notOre` | Nothing here can be mined. There is no art to ban and nowhere to walk, so it is an ending |
| `tooFar`, `notSeen` | The shard refusing a swing aimed at where you stand. Neither is answerable by moving, so both stop |
| `packFull` | Consolidate — the item cap, not the weight |
| `wornOut` | The pickaxe broke; the next cycle equips a spare |
| `saving` | Sit out the world save; nothing is learned and no counter is held against it |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | The shard declined to start the swing. Backed off like a throttle, but counted |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

**It does not move.** Not to a better tile, and not to the beetle: it smelts through `smeltHere`,
which uses a beetle already inside `SMELT_RANGE` and otherwise keeps the ore as ore and says so.
`smeltAll`'s walk is tree-shaken out of the bundle along with it, so `dist/mine-here.js` contains no
`player.run` at all — the promise is a property of the file rather than of the loop.

That is what makes weight a real ending here. `dist/mining.js` empties its pack on every spot that
runs dry and walks to the beetle to do it; this one only ever has the spot it is standing on. If it
stops saying *smelting freed nothing — the beetle has to be standing next to you*, that is what it
means: call the beetle over and paste it again.

### Before you paste it

- **Stand on the vein**, within swinging distance. The run will not go looking for one, and a first
  swing that comes back `nothingNearby` ends it — saying so, since a worked-out message from a run
  that never landed a swing means you were in the wrong place rather than that the mountain is spent.
- **The fire beetle within `SMELT_RANGE`**, and yours. Further off and the ore simply stays ore.
- A pickaxe in hand, spares in the pack. Being mounted is fine.
- `ORE_TILE_GRAPHICS`, `SCAN_RADIUS`, `MINE_RANGE`, `RESPAWN_DELAY`, `MAX_STEPS` and
  `NOTHING_NEARBY_HINT` are not read by this script at all. Everything else in
  [`config.ts`](config.ts) applies as written.

Heartbeat and world-save lines still say `mining:` — those modules are shared, and both scripts are
mining. The loop's own lines say `mine-here:`.

## What to set

Everything lives in [`config.ts`](config.ts). Values re-exported from
[`lib/timings.ts`](../lib/timings.ts) at the top of that file are shared with lumberjacking; to give
mining its own, delete it from the re-export list and declare it below.

The tables below cover what is worth changing. The rest of the re-exported list is plumbing that
should not need touching — `STEP_DELAY`, `WALK_DELAY`, `TARGET_TIMEOUT`, `IDLE_POLL`,
`THROTTLE_BACKOFF` / `THROTTLE_BACKOFF_MAX`, and the `SAVE_*` / `SAVING_TEXT` values that sit out a
world save. They are commented in `lib/timings.ts` where they are declared.

### Finding the ore

| Setting | What it is for |
| --- | --- |
| `ORE_TILE_GRAPHICS` | **The important one.** The land tiles the shard calls a mountain or a cave floor. Fill it in from `dist/mine-probe.js` |
| `NOT_ORE_GRAPHICS` | The override, and a seed only — a refusal learned on the shard goes to the run's memory, not back here. Put a graphic in it if the script keeps swinging at something that is not a vein |
| `ORE_STATIC_NAME` | `/cave\|rock\|mountain\|ore/i`. Cave floors are *statics*, and those the client can name. Wider than it looks — `rock` also names the pebbles scattered over half the world — but that is the cheap direction: the first swing at one gets `notOre`, the art is banned, and its copies stop being walked to |
| `ORE_GRAPHICS` | The arts an ore pile is drawn with. A set to match against and nothing more — never a way to read a stack's size |
| `ORE_NAME` | `/\bore\b/i`, the fallback for a shard whose ore wears an unknown art. A whole word: `ore` inside `sycamore` would put something in the smelter that was never meant to go there |
| `MINE_RANGE` | 2. Where walking stops and swinging starts — not a range the shard enforces, since the swing names no tile |
| `SCAN_RADIUS`, `PROBE_RADIUS`, `SURVEY_ARTS` | How far the loop looks, how far the probe looks, and how many arts the loop lists on a dead end |
| `RESPAWN_DELAY` | 25 minutes. The knob to turn if the script comes back to a vein that is still empty |

### The tool

| Setting | What it is for |
| --- | --- |
| `PICKAXE_NAME` | `'pickaxe'`. Matched against the name; the graphic is learned from the one you start holding |
| `SPARE_BAG_SERIAL` | Pin the bag the spares live in. Worth setting if they are in a bag inside another bag — the search opens the top level of the pack and no deeper |
| `DIG_TIMEOUT` | 8s. A swing plays its animation before the result arrives, so this has to outlast the animation |
| `EQUIP_ATTEMPTS`, `EQUIP_POLL`, `EQUIP_TIMEOUT` | Equip pacing, shared with lumberjacking |

### Smelting

| Setting | What it is for |
| --- | --- |
| `FIRE_BEETLE_GRAPHICS` | `0xa9` is the stock body. The search logs the name and body of whatever it finds, so a wrong guess is visible rather than silent |
| `FIRE_BEETLE_SERIAL` | Pins one exactly and skips the search |
| `BEETLE_SCAN_RADIUS`, `SMELT_RANGE`, `MAX_BEETLE_STEPS` | How far to look, how close to stand, how long to spend walking there |
| `MIN_SMELT_AMOUNT` | 2. Two ore make an ingot, so a stack of one cannot be smelted at all and the refusal is silent — see below |
| `SMELT_ATTEMPTS` | 3. Silent failures in a row before giving up on a hue. More than one, because a throttled or stale attempt also looks silent |
| `MAX_SMELT_PASSES`, `SMELT_DELAY`, `SMELT_TIMEOUT`, `SMELT_POLL` | Smelting loop bounds and pacing |
| `COMBINE_DELAY`, `ORE_SETTLE_TIMEOUT`, `ORE_SETTLE_POLL` | Consolidation pacing, and how long to wait for a swing's ore to turn up |
| `INGOT_GRAPHICS` | Re-exported from [`lib/arts.ts`](../lib/arts.ts). A seed only — the real graphic is learned by diffing the pack across the first successful smelt |
| `DISMOUNT_TIMEOUT`, `DISMOUNT_POLL`, `DISMOUNT_ATTEMPTS` | Getting off the mount |

### Reading the journal

`OUTCOME_TEXT` maps journal phrases to the branches in the table above. It ships as stock RunUO
wording — a hypothesis, not a fact. Correct it against your shard's journal after the first run: a
phrase that never matches shows up as an `unknown` outcome, which stops the run, rather than as a
silent wrong turn. `empty` and `nothingNearby` are the two worth getting right, since between them
they decide whether the character parks a tile or walks away.

`UNSKILLED_TEXT` and `THROTTLED_TEXT` are checked by the smelt, which has no outcomes of its own.

### Stopping

| Setting | Default | What it is for |
| --- | --- | --- |
| `MAX_CYCLES` | | The backstop on the whole run |
| `MAX_UNKNOWN` | | Unreadable outcomes in a row before stopping |
| `MAX_THROTTLED` | | Refusals in a row before stopping |
| `STALL_WARN` / `STALL_STOP` | | Cycles without a swing landing before it warns, then stops |
| `PACK_LIMIT` | 120 | The item-cap guard. There is deliberately **no** weight guard — see below |
| `NOTHING_NEARBY_HINT` | 5 | Empty spots in a row before it says `ORE_TILE_GRAPHICS` is probably wrong and lists what is underfoot |
| `HEARTBEAT_EVERY`, `LOG_EVERY`, `IDLE_LOG_EVERY` | | How often it says it is still alive |

## When it goes wrong

**`no ore in range` while standing on a mountain.** The likeliest failure, and it means
`ORE_TILE_GRAPHICS` does not match this shard's tile numbering. The stop prints the commonest arts
under your feet with `MATCHES` against the ones the config accepts — those are the ones to correct.
Run `dist/mine-probe.js` for the full list.

**Five spots in a row with nothing to harvest.** Same cause, caught earlier. The run says so once
and lists the arts underfoot.

**`unreadable outcome, check OUTCOME_TEXT`.** The shard words its harvest messages differently.
Read the journal after a swing and correct `OUTCOME_TEXT`.

**`overweight … and smelting freed nothing`.** No beetle in range, a beetle that is not yours, or
every hue written off. The run clears the write-offs and tries once more before giving up.

**`could not get off the mount`.** Double-clicking yourself is not how this shard dismounts. It
reissues `DISMOUNT_ATTEMPTS` times and then stops saying so, rather than mining on regardless.

**`no pickaxe`.** Nothing in hand and no spare found. If the spares are in a nested bag, pin
`SPARE_BAG_SERIAL` — the failure path logs every graphic the search saw, one level down included.

## Notes on the shard

Written against UOAlive.

- **Ore piles come in four arts** (`0x19B7`, `0x19BA`, `0x19B9`, `0x19B8`), which the stock tables
  call the 1, 2, 3 and 4+ stack sizes. **They are not that here** — a pile of 33 arrives wearing the
  one the tables call a single. So the arts are a set to match against and nothing more: ore is
  grouped by hue, never by graphic, and a stack's size is read from `item.amount` alone.
- Ore is consolidated by double-clicking one pile and targeting another, which is what works by hand
  there. A combine consumes one of the two piles, so the pack is rescanned between passes rather
  than planned up front.
- **A swing's ore arrives as a new pile** rather than joining the one already in the pack, so
  consolidating only when something complains lets one pile per swing pile up. It is done after
  every swing that produced ore instead, which keeps the pack at one pile per hue: the item cap is
  then never approached by pile count alone — and hitting it *destroys* the swing's ore rather than
  dropping it — and nothing is left sitting below `MIN_SMELT_AMOUNT` when the smelt comes. The cost
  is one combine gesture plus `COMBINE_DELAY` on the swings that produce a second pile.
- The ore lands *after* the journal line announcing it, so grouping the instant a swing reads `dug`
  can consolidate a pack the new pile has not turned up in yet. `waitForOre` polls for it first, and
  reads the ore **total** rather than the number of piles — a shard that does merge the ore on
  arrival then satisfies it immediately instead of waiting out `ORE_SETTLE_TIMEOUT` every swing.
- **The dig names no tile at all: it answers the cursor with `waitTargetSelf` and lets the shard
  pick the ore.** That is what works by hand here, and it sidesteps every way an explicit
  `target.terrain` can be wrong — land versus static, and which of the several arts stacked on one
  tile is the one actually carrying ore. [`vein.ts`](vein.ts) still finds and books tiles, but its
  job is deciding where to *stand*: `MINE_RANGE` is the distance at which walking stops and swinging
  starts, not a range the shard enforces. `dist/mine-here.js` is what falls out of taking that
  seriously — a character already standing on a vein needs no scan, no walk and no tile numbering.
- **Trees can be identified by name and ore cannot.** `client.getStatic` reads the *static*
  tiledata, so lumberjacking can ask the client whether an art is called a tree; a mountainside is a
  land tile, and `client.getTile` answers with flags and no name at all. `ORE_TILE_GRAPHICS` is
  therefore a graphic table rather than a name match, seeded with the stock RunUO mountain and cave
  bands. `dist/mine-probe.js` prints every distinct art around you with its `isLand` flag and tile
  count, which is what the table should actually be filled in from.
- **Land and static tiledata are numbered in separate tables**, so 1339 is a mountain band as land
  and a cave floor as a static. Everything in `vein.ts` that keys on an art keys on the kind too —
  the runtime ban is `land:231` rather than `231`, or one ban would hide an unrelated art.
- **A learned refusal has to outrank the seeded table.** Lumberjacking's `isTree` can afford to
  check its overrides first because `TREE_GRAPHICS` ships empty; `ORE_TILE_GRAPHICS` ships full, so
  asking it first made `markNotMineable` silently do nothing at all — the ban was recorded and then
  ignored on the very next scan. `isOre` asks the bans first and the seed second.
- **A fire beetle is a portable forge, and the smelt is the inverse of making boards.** Boards are
  the tool used and the resource targeted; smelting is the *ore* double-clicked and the *beetle*
  targeted. It is never double-clicked itself — it is rideable, so that mounts you.
- **Mining has to get off the mount first**, which is awkward precisely because the fire beetle is
  both the ride out and the smelter once you arrive. There is no dismount call in this API:
  [`mount.ts`](mount.ts) double-clicks the player and polls `equippedItems.mount` until it clears.
- **Ore destroyed by a full pack is not ore dropped on the floor.** `packFull` has its own
  `OUTCOME_TEXT` bucket, and it triggers a consolidation rather than another swing: the container
  hit its item cap, so forty piles of one becoming one pile of forty is the fix that gives back
  thirty-nine slots. Lumberjacking needs no equivalent — logs stop it on weight long before the
  item cap.
- **Smelting is triggered by a spot running dry** — the `empty` and `nothingNearby` outcomes, which
  are the same event at two scopes because the swing aims by where the character stands rather than
  by naming a tile.
  - This was originally weight and nothing else, on the reasoning that a depleted vein says nothing
    about how full the pack is and that walking to the beetle every time one runs dry is a lot of
    walking. Both are still true; what changed is the judgement about which cost is worth paying.
  - Weight stays as the **backstop**, because nothing says a run has to work a spot out before it
    caps, and `guards.ts` has *no* weight check to catch one that does. A guard at the usual buffer
    below the limit would fire first, every time, and the smelt would never happen at all. What ends
    an overweight run is a smelt that freed nothing.
  - Still not a finishing step: what is in the pack when the loop exits is the few swings since the
    last dry spot, and a run that ended on a stop reason has usually ended because something is
    wrong. `groupOres()` on the way out, `smeltAll()` only if it is ending over the limit.
- **A refusal is not a verdict on the material.** The conversions have no outcomes to read, so the
  shard's action throttle reaches them as silence — and three silent passes write a hue off for the
  rest of the run. A live run lost 86 ore of one colour that way. `THROTTLED_TEXT` is checked before
  a miss is counted, and shared with `OUTCOME_TEXT.throttled` so one correction fixes both.
- **The fire beetle wanders, and a smelt aimed at one out of range fails silently** — identical to
  an ore that cannot be worked. `smeltAll` proves it is in range once, with the walk; `forgeGone`
  re-reads its position before each pass and ends the pass instead of blaming the ore. It is asked
  only once a stack has been chosen, so a pack with nothing to smelt still reports itself clear
  without a beetle, a forge or a walk — which is what makes smelting on every dry vein affordable.
- **`item.amount` is 0 for a stack the client has no data for**, not 1 and not absent — so a size
  test written as `amount >= 2` skips *every* pile in the pack, and the run halts overweight beside
  a working beetle with ore it could have smelted. An unknown size is therefore worth one attempt,
  and only a size the client has actually reported as one is skipped.
- **Two ore make an ingot, so a stack of one cannot be smelted at all** — and the shard's refusal is
  silent, which in the pack diff is indistinguishable from a throttled attempt. Offered anyway, a
  lone ore burns `SMELT_ATTEMPTS` and then writes off the whole *hue*, taking every future stack of
  it along with it. `MIN_SMELT_AMOUNT` skips it by size instead, and remembers nothing: `groupOres`
  piles the hue together first, so whatever is still at one afterwards is genuinely the odd ore out,
  and the next swing that lands on that vein makes it two.
- **Ore is matched by graphic first and tooltip name second**, `\bore\b` as a whole word on the
  precedent of the key search in [`src/boxes`](../boxes/README.md) — `ore` at the end of *sycamore*
  would put something in the smelter that was never meant to go there. An art learned that way joins
  `ORE_GRAPHICS`, so it costs one tooltip and then goes back to being a graphic lookup. It exists
  because the seeded arts come from the stack-size table this shard is already known to disagree
  with.
- **A hue written off after three silent passes is a verdict worth reopening.** A beetle that
  stepped out of range, a run of throttled attempts and a stack that was briefly too small all look
  identical to an ore that cannot be worked. When the alternative is ending the run overweight,
  `retryUnsmeltable()` clears the write-offs for one more go; it returns false once there is nothing
  left to reconsider, which is what keeps that from looping.
- **A condition is checked where it is decided, not again where it is acted on.** A live run smelted
  nothing at all because the loop decided it was overweight and then called a helper that asked
  `tooHeavy()` a second time — by which point the answer had changed, so the smelt was skipped and
  the run stopped for being overweight without ever having tried.
- **The proof that a smelt landed is ore leaving the pack, not weight going down.** `player.weight`
  can still be reporting its pre-smelt figure when the pack diff has already confirmed the
  conversion, and reading that as *smelting freed nothing* ended runs that were working fine.
- **Mining has no bounds box, and the one it inherited stopped every run on cycle zero.** The folder
  was seeded with lumberjacking's forest rectangle, and `stopReason()` runs before the scan, the
  equip and the swing — so a character standing anywhere else exited immediately, having done
  literally nothing. Lumberjacking keeps its box because a forest is a place you work; mining roams.
- **"There are no harvestable resources nearby" is about the area, not a tile** — the last word is
  the whole point, and it is the answer a swing that names no tile mostly gets. It has its own
  `OUTCOME_TEXT` bucket, and it parks every ore tile within `MINE_RANGE` on the respawn cooldown at
  once, which is what makes the character walk away. Before it had a bucket it read as an unreadable
  outcome: the character stood still, swung five times for the same sentence, and the run stopped.
  Parking only the vein the scan had picked would have done the same thing more slowly.
- **A run of empty spots is what a wrong `ORE_TILE_GRAPHICS` looks like from the outside.** The scan
  keeps finding ore because the table says the ground is ore; the shard keeps disagreeing. After
  `NOTHING_NEARBY_HINT` spots in a row the run says so once and lists the arts under the character's
  feet.
- **A dead end has to say what it saw.** `no ore in range` while standing on a mountain is
  unactionable on its own, so the stop prints the commonest arts under your feet and marks which
  ones the config matches. [`survey.ts`](survey.ts) is that listing, shared with the probe.

### Known unverified

- **`ORE_TILE_GRAPHICS`**, which is the one that matters. The bands are copied from the stock RunUO
  mountain and cave tables and nothing has confirmed them against UOAlive.
- `OUTCOME_TEXT`, on the same footing — stock RunUO phrasing as a hypothesis. `empty` matters most:
  it is what parks a vein for `RESPAWN_DELAY`, so a wrong phrase there means the script keeps
  swinging at a worked-out tile until the unknown-outcome count stops the run.
- **Three phrasings that do not obviously agree with lumberjacking's.** `'You cannot mine there'`
  sits in the `empty` bucket, so it parks the tile for `RESPAWN_DELAY`; on most shards that sentence
  means the tile is not mineable at all, which is `notOre` and a permanent ban. `'There is nothing
  here to harvest'` (`nothingNearby`) and `'There is no ore here to mine'` (`empty`) are close enough
  that a shard using a hybrid wording lands in whichever key `Object.keys` reaches first, and `empty`
  precedes `nothingNearby`. Both are one journal line from being settled.
- `RESPAWN_DELAY`. 25 minutes, chosen to match lumberjacking's `REGROW_DELAY` and not measured. The
  console names every tile it parks and when it expects it back.
- The fire beetle body in `FIRE_BEETLE_GRAPHICS` (`0xa9`). The search logs the name and body of
  whatever it settles on, and `FIRE_BEETLE_SERIAL` pins one exactly if the guess is wrong.
- Whether a fire beetle actually smelts by being targeted with an ore stack on this shard, and
  whether it has to be yours. `isRenamable` is what tells your pet from a stranger's, and the smelt
  falls back to any beetle in range if none of them read as yours.
- Whether double-clicking yourself is how this shard dismounts. If it is not, `mount.ts` reissues
  three times and then stops the run saying so, rather than mining on regardless.
- Whether the shard merges ore piles of differing graphics. `groupOres` logs and bails rather than
  looping if a combine makes no progress.
- Whether the `notOre` branch wants to mark the tile as well as the art. It calls
  `markNotMineable(vein)` and `markUnusable(vein, ...)` both, and once the art is banned the tile
  ban can never be reached — harmless, but it double-logs, and if the two ever disagree it is the
  art ban that is right.
- Whether the ingot arts in [`lib/arts.ts`](../lib/arts.ts) are the right four. Nothing has confirmed
  them against the shard; mining only reads the set to avoid re-logging an art it has already
  learned, so nothing depends on the answer.
