# mining — dig ore, smelt it on a fire beetle

Builds two scripts:

| Script | What it does |
| --- | --- |
| `dist/mining.js` | Walks to the nearest vein, swings, consolidates the ore, and smelts it against a fire beetle |
| `dist/mine-here.js` | Stands still and works the spot you are on until it runs dry, then smelts and stops |

**`ORE_TILE_GRAPHICS` ships as a stock RunUO guess** and it is the one setting most likely to be
wrong for your shard. Everything else degrades gracefully; this one ends runs — for `dist/mining.js`,
at least. `dist/mine-here.js` never reads it, and a dead-end run prints the arts it actually saw.

## Why it exists

A full pack of ore is twelve stones a piece, and getting it to a forge means walking back to town. A
**fire beetle** is a portable forge: it is a pet, it follows you, and an ore stack double-clicked and
targeted at one comes back as ingots. That is why this script never walks to town — and also why it
has to get off the mount first, since the beetle is usually both the ride out and the smelter.

Unlike lumberjacking there is **no bounds box**. Mining roams; what keeps a run somewhere sensible is
where the ore is.

## What `dist/mining.js` does

Before the loop: get off the mount, open the beetle cursor, consolidate the pack, and smelt if it is
already over the limit — in that order, so a run pasted with a full pack can take its first swing and
the beetle you click is one standing next to you rather than the one you were sitting on.

Every cycle:

1. **Check the stop conditions** — dead, or the pack at its item cap.
2. **Sit out a world save.** The shard stops answering for a few seconds, and every step below reads
   that silence as its own kind of failure. The wait always says how it ended — the shard's
   completion line, `SAVE_WAIT` running out, or the run having a reason to stop.
3. **Get off the mount.** Asked every cycle, so a remount costs one cycle rather than the rest of the
   run. There is no dismount call in this API: it double-clicks the player and polls
   `equippedItems.mount` until it clears.
4. **Equip a pickaxe.** Also every cycle. Spares are found in the pack, one level of bags down.
5. **The weight backstop.** If the pack is genuinely over the limit, smelt now.
6. **Scan for a vein** within `SCAN_RADIUS` *and* `MINE_Z_RANGE` of your own elevation, nearest
   first, skipping tiles the run has parked.
7. **Walk to it** if it is further than `MINE_RANGE`. One naive `Math.sign` step per cycle; there is
   no pathfinding API. A vein that takes more than `MAX_STEPS` is marked unreachable for
   `UNREACHABLE_DELAY`.
8. **Swing**, and branch on what the shard says.

Steps 1-5 and 8, along with the counters that end a run, are
[`lib/harvest.ts`](../lib/harvest.js)'s `runHarvest` — the same loop `dist/mine-here.js` and
`dist/lumberjack.js` run. Steps 6 and 7 are `createApproach` in [`lib/tiles.ts`](../lib/tiles.ts).
What this folder supplies is the wordings, the tool, the smelt, and the outcomes in the table below.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per metal |
| `empty` | Park that tile for `RESPAWN_DELAY`, **and smelt** — the spot has run dry |
| `nothingNearby` | Park *everything* within `MINE_RANGE`, so the next scan looks further and the character walks off. **And smelt** |
| `notOre` | Ban the whole graphic, not just the tile — a wrong band in `ORE_TILE_GRAPHICS` is a whole stretch of mountain |
| `tooFar` | The shard disagreeing about the range. Set the tile aside rather than swinging again |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `packFull` | Consolidate. Forty piles of one becoming one pile of forty gives back thirty-nine slots |
| `wornOut` | The pickaxe broke; the next cycle equips a spare |
| `saving` | The shard is writing its world file. Sit it out; no counter is held against it |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | No cursor, and the journal explained nothing. Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

**When it smelts:** on a spot running dry, not on a schedule and not at the end. The character is
about to walk somewhere else anyway and the beetle has been following it, so that is the cheapest
moment in the run to convert. It costs nothing on the passes with nothing to do, because `smeltAll`
asks whether any pile is worth smelting *before* it looks for the beetle.

### Before you paste it

- Stand on the mountain face or in the cave you mean to work.
- **A pickaxe in hand.** The run learns its graphic from what you are holding. Spares go in the pack
  or in one bag inside it — `SPARE_BAG_SERIAL` pins a bag nested deeper than that.
- **The fire beetle nearby**, and yours. It opens a cursor at startup for you to click it — ESC to
  let the script find one instead. Without a beetle the run still mines; it stops when the pack fills,
  saying smelting freed nothing.
- Being mounted is fine — it gets off by itself.

### How to run it

```bash
npm run build
```

Paste `dist/mining.js`. The first thing the run prints is the world as it sees it — mounted or not,
what is in your hand, your weight — because a run that stops on its first cycle otherwise looks
exactly like a script that never started.

## What `dist/mine-here.js` does

The stationary half of `dist/mining.js`. It stands where you put it, swings until the shard says
there is nothing left, smelts what it mined, and stops. Same prologue: off the mount, the beetle
cursor, then a consolidation and a smelt if the pack arrives over the limit.

It runs the same `runHarvest` as `dist/mining.js`, and simply passes it no `approach`: it can leave
out the scan, the walk, the block map and the respawn wait because [`dig.ts`](dig.ts) answers the
target cursor with *yourself* and lets the shard pick the ore — so a swing is aimed by where the
character stands rather than by naming a tile, which is all [`vein.ts`](vein.ts) exists to decide.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per metal |
| `empty`, `nothingNearby` | **The spot is worked out.** Consolidate, smelt, and stop. One branch, not two — the pair differ by scope, and scope only matters to a run with somewhere else to walk |
| `notOre` | Nothing here can be mined. No art to ban and nowhere to walk, so it is an ending |
| `tooFar`, `notSeen` | Neither is answerable by moving, so both stop |
| `packFull` | Consolidate — the item cap, not the weight |
| `wornOut` | The pickaxe broke; the next cycle equips a spare |
| `saving` | Sit out the world save |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | Backed off like a throttle, and stops after `MAX_NO_CURSOR` |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run |

**It does not move.** Not to a better tile, and not to the beetle: it smelts through `smeltHere`,
which uses a beetle already inside `SMELT_RANGE` and otherwise keeps the ore as ore and says so.
`smeltAll`'s walk is tree-shaken out along with it, so `dist/mine-here.js` contains no `player.run`
at all — the promise is a property of the file rather than of the loop.

That is what makes weight a real ending here. If it stops saying *smelting freed nothing — the beetle
has to be standing next to you*, call the beetle over and paste it again.

### Before you paste it

- **Stand on the vein**, within swinging distance. A first swing that comes back `nothingNearby` ends
  the run — and says so, since a worked-out message from a run that never landed a swing means you
  were in the wrong place.
- **The fire beetle within `SMELT_RANGE`**, and yours. Further off and the ore stays ore.
- A pickaxe in hand, spares in the pack. Being mounted is fine.
- `ORE_TILE_GRAPHICS`, `SCAN_RADIUS`, `MINE_RANGE`, `MINE_Z_RANGE`, `RESPAWN_DELAY`, `MAX_STEPS`
  and `NOTHING_NEARBY_HINT` are not read by this script at all.

Heartbeat and world-save lines still say `mining:` — those modules are shared. The loop's own lines
say `mine-here:`.

## Trouble

The shard runs encounters that spawn monsters at anyone macroing AFK. Every cycle — and every slice
of an idle wait, which is where a run stands still longest — the loop checks four things: a hostile
mobile within `THREAT_RANGE`, your health going down, your beetle's health going down, and any
wording in `ATTACK_TEXT`. Any one of them opens an episode: it says `guards`, up to `GUARD_CALLS`
times, one call per `GUARD_CALL_DELAY`, and goes on mining. The count resets when a check comes back
clear, so something that comes back gets a fresh set of calls.

**None of it ends a run.** `dead` is still the only thing that stops one for combat reasons. If you
would rather it stopped at a health floor, `hurt(fraction)` is already in
[`lib/guards.ts`](../lib/guards.ts) and goes into this folder's `stopReason` in one line.

**There is no way to ask whether the guards can hear you.** The first call of a run says what it can
work out — a boundary wording in the journal, or an invulnerable human in sight — and neither is
authoritative. What is worth knowing: on stock RunUO the guard call answers criminal *players*, not
wild monsters, so a spot outside a town may do nothing with this at all. `NO_GUARDS_TEXT` is how a
shard that says so gets the run to stop wasting the breath.

## What to set

Everything lives in [`config.ts`](config.ts). Values re-exported from
[`lib/timings.ts`](../lib/timings.ts) at the top of that file are shared with lumberjacking; to give
mining its own, delete it from the re-export list and declare it below.

### Finding the ore

| Setting | What it is for |
| --- | --- |
| `ORE_TILE_GRAPHICS` | **The important one.** The land tiles the shard calls a mountain or a cave floor. Fill it in from what a dead-end run lists |
| `NOT_ORE_GRAPHICS` | The override, and a seed only — a refusal learned on the shard goes to the run's memory, not back here |
| `ORE_STATIC_NAME` | `/cave\|rock\|mountain\|ore/i`. Cave floors are *statics*, and those the client can name. Wider than it looks — `rock` also names the pebbles scattered over half the world — but that is the cheap direction: the first swing at one gets `notOre` and the art is banned |
| `ORE_GRAPHICS` | The arts an ore pile is drawn with. A set to match against and nothing more — never a way to read a stack's size |
| `ORE_NAME` | `/\bore\b/i`, the fallback for a shard whose ore wears an unknown art. A whole word: `ore` inside `sycamore` would put something in the smelter |
| `MINE_RANGE` | 2. Where walking stops and swinging starts — not a range the shard enforces, since the swing names no tile |
| `MINE_Z_RANGE` | 20. How far above or below you a tile may sit and still be worth walking to. A mountain face 40 z up passes the 2D distance test and the walk at it never closes |
| `SCAN_RADIUS`, `SURVEY_ARTS` | How far the loop looks, and how many arts it lists on a dead end |
| `RESPAWN_DELAY` | 25 minutes. The knob to turn if the script comes back to a vein that is still empty |

### The tool

| Setting | What it is for |
| --- | --- |
| `PICKAXE_NAME` | `'pickaxe'`. Matched against the name; the graphic is learned from the one you start holding |
| `SPARE_BAG_SERIAL` | Pin the bag the spares live in. Worth setting if they are in a bag inside another bag |
| `DIG_TIMEOUT` | 8s. A swing plays its animation before the result arrives |
| `DIG_TARGET_TIMEOUT`, `DIG_TARGET_POLL` | 4s and 100ms. How long to watch for the cursor before reading the swing as refused, and how often |
| `DIG_PROMPT_TEXT` | **The sentence the shard opens the cursor with.** Waited on as the cursor itself, because `target.open` cannot be relied on — get this wrong and every swing reports `no target cursor` |
| `EQUIP_ATTEMPTS`, `EQUIP_POLL`, `EQUIP_TIMEOUT` | Equip pacing, shared with lumberjacking |

### Smelting

| Setting | What it is for |
| --- | --- |
| `FIRE_BEETLE_GRAPHICS` | `0xa9` is the stock body. The search logs the name and body of whatever it finds |
| `FIRE_BEETLE_SERIAL` | Pins one exactly and skips the search |
| `PICK_BEETLE` | On by default: a cursor at startup to click your beetle, ESC to fall back to the search. A picked beetle is pinned |
| `BEETLE_SCAN_RADIUS`, `SMELT_RANGE`, `MAX_BEETLE_STEPS` | How far to look, how close to stand, how long to spend walking there |
| `MIN_SMELT_AMOUNT` | 2. Two ore make an ingot, so a stack of one cannot be smelted and the refusal is silent |
| `SMELT_ATTEMPTS` | 3. Silent failures in a row before giving up on a hue. More than one, because a throttled or stale attempt also looks silent |
| `MAX_SMELT_PASSES`, `SMELT_DELAY`, `SMELT_TIMEOUT`, `SMELT_POLL` | Smelting loop bounds and pacing |
| `COMBINE_DELAY`, `ORE_SETTLE_TIMEOUT`, `ORE_SETTLE_POLL` | Consolidation pacing, and how long to wait for a swing's ore |
| `COMBINE_TIMEOUT`, `COMBINE_POLL` | How long to poll the pack for the proof a combine landed |
| `MAX_COMBINE_ATTEMPTS` | Combines per consolidation. Bounds a pack holding several metals |
| `ORE_METALS` | Stock RunUO's nine metal names. A metal this shard has that these do not joins the set off its first tooltip |
| `ORE_METAL_LINE`, `NOT_METAL_TEXT` | Which tooltip line is the metal: letters only, and not one of the flags every item can carry |
| `OPL_TIMEOUT`, `METAL_MISSES` | How long to wait for a pile's tooltip, and how many unanswered ones before the lookup stops costing that wait |
| `METAL_ASKS` | Passes a pile's tooltip is waited for before it is grouped unnamed and left to the refusal |
| `DIFFERENT_ORE_TEXT` | The shard refusing two piles as different metals. The backstop for a pile no tooltip named — get it wrong and the run keeps two of those apart, and says so |
| `INGOT_GRAPHICS` | Re-exported from [`lib/arts.ts`](../lib/arts.ts). A seed only — the real graphic is learned by diffing the pack |
| `DISMOUNT_TIMEOUT`, `DISMOUNT_POLL`, `DISMOUNT_ATTEMPTS` | Getting off the mount |

### Reading the journal

`OUTCOME_TEXT` maps journal phrases to the branches above. It ships as stock RunUO wording — a
hypothesis, not a fact. Correct it against your shard's journal after the first run: a phrase that
never matches shows up as an `unknown` outcome, which stops the run, rather than as a silent wrong
turn. `empty` and `nothingNearby` are the two worth getting right, since between them they decide
whether the character parks a tile or walks away.

`UNSKILLED_TEXT` and `THROTTLED_TEXT` are checked by the smelt, which has no outcomes of its own.

### Trouble

| Setting | Default | What it is for |
| --- | --- | --- |
| `WATCH_FOR_TROUBLE` | true | The whole feature. Off, and none of the rest is read |
| `HOSTILE_NOTORIETY` | Gray, Criminal, Enemy, Murderer | Which healthbar colours count. Innocent is out, or every blue NPC in the world is trouble |
| `CALL_ON_SIGHT_NOTORIETY` | Criminal, Enemy, Murderer | Which of those are worth a `guards` on sight alone. Gray is out: the wildlife is gray, and a cat wandering past is not evidence of anything. A gray still draws the call the moment it damages you or the pet |
| `THREAT_RANGE` | 12 | How close it has to be. `selectEntity` takes no range of its own, so this is the only filter |
| `GUARD_CALL` | `'guards'` | What gets said |
| `GUARD_CALLS` | 3 | Calls per episode, `0` for no cap. The count resets the first cycle that sees nothing |
| `GUARD_CALL_DELAY` | 10s | The gap between them |
| `NO_GUARDS_TEXT` | | The shard saying the call is pointless here. One match and the run stops calling for good |
| `ATTACK_TEXT` | empty | Journal wordings that mean you are being attacked. Fill it in from your shard's journal |
| `GUARD_ZONE_TEXT`, `UNGUARDED_TEXT` | | The region boundary wordings, read only to say what protection you look to have |
| `GUARD_REPLY_WAIT` | 800ms | How long to watch for `NO_GUARDS_TEXT` after a call |

### Stopping

| Setting | Default | What it is for |
| --- | --- | --- |
| `MAX_CYCLES` | | The backstop on the whole run |
| `MAX_UNKNOWN` | | Unreadable outcomes in a row before stopping |
| `MAX_THROTTLED` | | Refusals in a row before stopping |
| `MAX_NO_CURSOR` | 20 | Swings the shard opened no cursor for, in a row, before stopping |
| `STALL_WARN` / `STALL_STOP` | | Cycles without a swing landing before it warns, then stops |
| `PACK_LIMIT` | 120 | The item-cap guard. There is deliberately **no** weight guard — see below |
| `NOTHING_NEARBY_HINT` | 5 | Empty spots in a row before it says `ORE_TILE_GRAPHICS` is probably wrong |
| `HEARTBEAT_EVERY`, `LOG_EVERY`, `IDLE_LOG_EVERY` | | How often it says it is still alive |

## When it goes wrong

**`no ore in range` while standing on a mountain.** The likeliest failure: `ORE_TILE_GRAPHICS` does
not match this shard's tile numbering. The stop prints the commonest arts under your feet with
`MATCHES` against the ones the config accepts.

**Five spots in a row with nothing to harvest.** Same cause, caught earlier.

**`unreadable outcome, check OUTCOME_TEXT`.** The shard words its harvest messages differently. Read
the journal after a swing and correct `OUTCOME_TEXT`.

**`no target cursor (n/20), backing off`.** The shard declined to start the swing and said nothing
about why. A few is ordinary; a run of them with a pickaxe in hand means the shard is refusing in a
wording `THROTTLED_TEXT` does not have. Add the wording and it becomes a throttle, which costs the
run nothing.

Since the swing waits on `DIG_PROMPT_TEXT` as well as on `target.open`, this now means the shard
asked for neither. If you can see *Where do you wish to dig?* on screen while the log says this, the
shard words its prompt differently — correct `DIG_PROMPT_TEXT` and it is fixed.

**`overweight … and smelting freed nothing`.** No beetle in range, a beetle that is not yours, or
every hue written off. The run clears the write-offs, consolidates and smelts once more before giving
up — once, not once per cycle, or a smelt that can never land spins in `smelting` until the stall
watchdog. Never a world save: that is waited out instead, both before the retry is spent and before
the verdict is drawn.

**`tooltips are not naming the metal here`.** No tooltip answered for three piles in a row, so the
run falls back to telling the metals apart the slow way — attempt a pair, read the refusal. Ordinary
on a shard with no OPL. If the metal *is* on screen and this still fires, the tooltip is arriving
slower than `OPL_TIMEOUT`.

**`save: nothing said in 60s, carrying on`.** No completion line arrived. Either the save really
did outlast `SAVE_WAIT`, or the shard words the end of it in a way `SAVE_DONE_TEXT` does not have —
read the journal after a save and correct it. Harmless in itself; the run carries on either way.

**`the tooltip lookup would not answer`.** The client threw out of `queryItemOPL` instead of
answering. Said once, and that pile keeps its metal unread; three in a row and the run falls back to
the refusal-driven grouping for good. Harmless on its own — before it was caught, it ended the run.

**`the shard refused two piles both read as 'x'`.** The line being read as the metal is not the
metal. Those piles go back to the refusal-driven grouping; correct `ORE_METAL_LINE` or
`NOT_METAL_TEXT` against what the tooltip actually shows.

**`could not get off the mount`.** Double-clicking yourself is not how this shard dismounts.

**`no pickaxe`.** Nothing in hand and no spare found. If the spares are in a nested bag, pin
`SPARE_BAG_SERIAL` — the failure path logs every graphic the search saw.

## Notes on the shard

Written against UOAlive.

- **Ore piles come in four arts** (`0x19B7`, `0x19BA`, `0x19B9`, `0x19B8`), which the stock tables
  call the 1, 2, 3 and 4+ stack sizes. **They are not that here** — a pile of 33 arrives wearing the
  one called a single. So the arts are a set to match against and nothing more, and a stack's size is
  read from `item.amount` alone.
- **The metal is its own tooltip line.** The pile is named `Ore`, weighed, and then the metal is
  printed under a divider — `Verite`. That is per-pile and costs no failed combine, so two metals are
  told apart before anything is double-clicked. A tooltip that answers and names no metal is *plain
  iron*, which is the distinction hue could never draw: `item.hue` reads 0 both for iron and for a
  pile whose properties the client has not been sent.
- **The refusal alone was never enough.** `DIFFERENT_ORE_TEXT` is remembered against a pair of
  serials, and every swing delivers a pile wearing a serial nothing has been learned about — so the
  run paid a refusal per metal per new pile. It is the backstop now, for piles no tooltip named; hue
  still orders those candidates, since it is right nearly always. A refusal is remembered for the run,
  a silent miss only for the pass — a busy moment must not split a metal for good.
- **A world save can start and finish inside one swing.** A dig waits up to `DIG_TIMEOUT`, so by the
  time the loop reads the journal the shard has usually said both that it was saving and that it was
  done. `waitOutSave` reads the completion *before* it clears the journal for exactly that reason —
  clearing first threw the line away and then stood still for the whole of `SAVE_WAIT`, once per
  save. The clear still happens, so the last save's completion cannot end the next one's wait.
- **A combine is silent whether it lands or not.** The proof is the pack: the consumed pile gone, or
  the pile it went into grown. Counting piles before and after read a client that had not refreshed
  yet as "no progress" and gave up with several piles of one metal still in the pack.
- **A swing's ore arrives as a new pile** rather than joining the one already in the pack, and it
  lands *after* the journal line announcing it. `waitForOre` polls for it, then `groupOres`
  consolidates: that keeps the pack at one pile per metal, so the item cap is never approached by pile
  count alone — hitting it *destroys* the swing's ore rather than dropping it — and nothing is left
  sitting below `MIN_SMELT_AMOUNT` when the smelt comes.
- **A vein is only somewhere to stand, so the scan filters by elevation.** `distanceTo` is
  Chebyshev over x and y, so a mountain face 40 z above you is "one tile away" and the walk at it
  never closes — it cost a cycle and an `UNREACHABLE_DELAY` write-off each time. Since the swing
  names no tile, the vein's z never reaches the shard and dropping those candidates changes only
  where the character walks. `MINE_Z_RANGE` is deliberately generous: the ore land tile legitimately
  stands above the ground you mine it from, and 0 would find nothing.
- **The dig names no tile at all: it answers the cursor with `waitTargetSelf`** and lets the shard
  pick the ore. That sidesteps every way an explicit `target.terrain` can be wrong — land versus
  static, and which of the several arts stacked on one tile carries the ore. `MINE_RANGE` is
  therefore the distance at which walking stops, not a range the shard enforces.
- **`target.open` is not reliable, and `target.wait`/`waitTargetSelf` are built on it.** A measured
  swing had the shard's prompt in the journal at 164 ms and `target.open` false for the whole six
  seconds after it. So the swing waits on `DIG_PROMPT_TEXT` *or* `target.open`, whichever comes, and
  then calls `target.self()` — which the client sends regardless of what it thinks its state is.
- **`target.cancel()` shortly before a swing costs that swing its cursor.** Same character, same
  tile: cancelled 300 ms before, `target.open` never went true and nothing was dug; after a two
  second gap it opened at 222 ms and dug. So the cancel is now conditional on a cursor being open.
- **The vein scan is `(2 * SCAN_RADIUS + 1)` squared `getTerrainList` calls** — 625 at the shipped
  radius — and it used to run immediately before every swing. `scanForVein` now keeps the tile it is
  working and re-reads that one tile, falling back to a `MINE_RANGE` box and only then the full one.
- **Trees can be identified by name and ore cannot.** `client.getStatic` reads the *static* tiledata;
  a mountainside is a land tile, and `client.getTile` answers with flags and no name. Hence a graphic
  table rather than a name match.
- **Land and static tiledata are numbered in separate tables**, so 1339 is a mountain band as land
  and a cave floor as a static. Everything that keys on an art keys on the kind too — the runtime ban
  is `land:231` rather than `231`, or one ban would hide an unrelated art.
- **A learned refusal has to outrank the seeded table.** `ORE_TILE_GRAPHICS` ships full, so asking it
  first made `markNotMineable` silently do nothing — the ban was recorded and ignored on the next
  scan. `isOre` asks the bans first and the seed second.
- **The smelt is the inverse of making boards.** Boards are the tool used and the resource targeted;
  smelting is the *ore* double-clicked and the *beetle* targeted. The beetle is never double-clicked
  itself — it is rideable, so that mounts you. Which is also why mining has to dismount first, and
  there is no dismount call in this API: [`mount.ts`](mount.ts) double-clicks the player and polls.
- **Ore destroyed by a full pack is not ore dropped on the floor.** `packFull` triggers a
  consolidation rather than another swing. Lumberjacking needs no equivalent — logs stop it on weight
  long before the item cap.
- **Smelting is triggered by a spot running dry**, with weight as the backstop. `guards.ts` has *no*
  weight check: a guard at the usual buffer below the limit would fire first, every time, and the
  smelt would never happen at all. What ends an overweight run is a smelt that freed nothing.
- **A refusal is not a verdict on the material.** The conversions have no outcomes to read, so the
  action throttle reaches them as silence — and three silent passes write a hue off for the rest of
  the run. A live run lost 86 ore of one colour that way. `THROTTLED_TEXT` is checked before a miss
  is counted, and shared with `OUTCOME_TEXT.throttled` so one correction fixes both.
- **The fire beetle wanders, and a smelt aimed at one out of range fails silently** — identical to an
  ore that cannot be worked. `forgeGone` re-reads its position before each pass and ends the pass
  instead of blaming the ore. It is asked only once a stack has been chosen, which is what makes
  smelting on every dry vein affordable.
- **`item.amount` is 0 for a stack the client has no data for**, not 1 and not absent — so a size
  test written as `amount >= 2` skips *every* pile in the pack. An unknown size is worth one attempt;
  only a size the client has actually reported as one is skipped.
- **Two ore make an ingot, so a stack of one cannot be smelted at all** — and the refusal is silent.
  Offered anyway, a lone ore burns `SMELT_ATTEMPTS` and writes off the whole *hue*.
  `MIN_SMELT_AMOUNT` skips it by size and remembers nothing: the next swing that lands makes it two.
- **Ore is matched by graphic first and tooltip name second**, `\bore\b` as a whole word — `ore` at
  the end of *sycamore* would put something in the smelter that was never meant to go there. An art
  learned that way joins `ORE_GRAPHICS`.
- **A hue written off after three silent passes is worth reopening.** A beetle briefly out of range,
  a run of throttled attempts and a stack that was too small all look identical to an ore that cannot
  be worked. `retryUnsmeltable()` clears the write-offs for one more go, and returns false once there
  is nothing left to reconsider — and once a retry has already been spent with nothing converting
  since, because `smeltAll` writes the same hues off again on the next cycle.
- **A condition is checked where it is decided, not again where it is acted on.** A live run smelted
  nothing because the loop decided it was overweight and then called a helper that asked `tooHeavy()`
  a second time, by which point the answer had changed.
- **The proof that a smelt landed is ore leaving the pack, not weight going down.** `player.weight`
  can still be reporting its pre-smelt figure when the pack diff has confirmed the conversion.
- **Mining has no bounds box, and the one it inherited stopped every run on cycle zero.** The folder
  was seeded with lumberjacking's forest rectangle, and `stopReason()` runs before the scan, the
  equip and the swing.
- **"There are no harvestable resources nearby" is about the area, not a tile** — the last word is
  the whole point, and it is the answer a swing that names no tile mostly gets. It parks every ore
  tile within `MINE_RANGE` at once, which is what makes the character walk away. Before it had a
  bucket the character stood still, swung five times for the same sentence, and the run stopped.
- **A run of empty spots is what a wrong `ORE_TILE_GRAPHICS` looks like from the outside**, and a
  dead end has to say what it saw. [`survey.ts`](survey.ts) is that listing.

### Known unverified

- **Everything the guard call rests on.** Whether `guards` is the phrase this shard takes, whether
  guards answer monsters here at all, and the wordings in `NO_GUARDS_TEXT`, `GUARD_ZONE_TEXT` and
  `UNGUARDED_TEXT` — all stock RunUO guesses.
- **`HOSTILE_NOTORIETY`**: whether this shard's encounter spawns come up gray or red. If they are
  gray they share a notoriety with every cat and crow, so the call waits for blood — put them in
  `CALL_ON_SIGHT_NOTORIETY` only if a gray in sight is worth shouting at here.
- Whether `client.selectEntity` disturbs the client's current target, and so whether the watch can
  cost a swing its cursor the way `target.cancel()` was found to.
- **`ORE_TILE_GRAPHICS`**, which is the one that matters. Copied from the stock RunUO mountain and
  cave tables, unconfirmed against UOAlive.
- `OUTCOME_TEXT`, on the same footing. `empty` matters most: it is what parks a vein for
  `RESPAWN_DELAY`.
- **Three phrasings that do not obviously agree with lumberjacking's.** `'You cannot mine there'` sits
  in `empty`, so it parks the tile; on most shards that sentence means the tile is not mineable at
  all, which is `notOre` and a permanent ban. `'There is nothing here to harvest'` and `'There is no
  ore here to mine'` are close enough that a hybrid wording lands in whichever key `Object.keys`
  reaches first.
- `RESPAWN_DELAY`. 25 minutes, chosen to match lumberjacking's `REGROW_DELAY` and not measured.
- **`MINE_Z_RANGE`**, on the same footing as `ORE_TILE_GRAPHICS`. 20 comes from the stock climb rule
  of about 2 z a step over `SCAN_RADIUS`, not from this shard. Too tight ends a run on `no ore in
  range` with the survey printing the mountain art beside `MATCHES`.
- The fire beetle body in `FIRE_BEETLE_GRAPHICS` (`0xa9`), and whether a beetle actually smelts by
  being targeted with an ore stack here, and whether it has to be yours. `isRenamable` is what tells
  your pet from a stranger's, and the smelt falls back to any beetle in range.
- Whether double-clicking yourself is how this shard dismounts.
- `DIFFERENT_ORE_TEXT`, the stock RunUO wording. A shard that words it differently reaches the
  grouping as silence, which splits the pair for the pass and logs `nothing was said`.
- Whether the `notOre` branch wants to mark the tile as well as the art. It calls both, and once the
  art is banned the tile ban can never be reached — harmless, but it double-logs.
- Whether the ingot arts in [`lib/arts.ts`](../lib/arts.ts) are the right four. Nothing depends on
  the answer.
