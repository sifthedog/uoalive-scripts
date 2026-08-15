# lumberjacking — chop trees, make boards, load the animals

Builds one script: `dist/lumberjack.js`.

> **This one has never been run.** `client.getTerrainList` and `client.getStatic` are used for the
> first time here, and most of `OUTCOME_TEXT` is stock RunUO wording taken as a hypothesis. Two
> phrases have since been confirmed from live *mining* runs — `notTree` and `notSeen` — and the rest
> are guesses. Wrong phrasing shows up as `unknown` outcomes, which stop the run after `MAX_UNKNOWN`
> rather than flailing.

## Why it exists

Chopping is a swing, a wait, and a walk to the next trunk, and the pack fills with logs that weigh
more than the boards they become. So the script does the whole cycle: work a patch of forest, turn
the logs into boards when the weight climbs, and put the boards on your pack animals so the run
keeps going instead of ending at the weight cap.

Unlike mining, it stays inside a **bounds box** — a forest is a place you work, and roaming out of it
is how a script ends up in a town or in the water.

## What it does

Every cycle:

1. **Check the stop conditions** — dead, outside `BOUNDS`, overweight, or the pack at its item cap.
2. **Equip an axe.** Axes are two-handed and hatchets one-handed, so it reads
   `equippedItems.twoHanded ?? equippedItems.oneHanded`.
3. **Haul, if the weight is over `HAUL_BUFFER`.** Boards are made first — an unconvertible wood
   still gets hauled, but a convertible one travels lighter — then every pack animal in range is
   walked to and filled, nearest first.
4. **Scan for a tree** within `SCAN_RADIUS`, nearest first, skipping tiles the run has parked and
   trees no legal standing tile could reach.
5. **Walk to it** if it is further than `CHOP_RANGE`. One naive `Math.sign` step per cycle, and a
   step that would leave the box falls back to whichever cardinal half stays inside — so the
   character slides along the edge rather than giving up.
6. **Chop**, and branch on what the shard says.

The outcome branches:

| Outcome | What the loop does |
| --- | --- |
| `chopped` | Count it and carry on |
| `empty` | Out of wood. Park that tile for `REGROW_DELAY` — a stump grows back |
| `notTree` | Ban the whole graphic. The tiledata over-reaches, and one refusal drops every copy of that art out of the scan at once |
| `tooFar` | The shard disagreeing about the range. Set the tile aside |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `wornOut` | The axe broke; the next cycle equips a spare |
| `saving` | The shard is writing its world file. Sit it out; nothing is learned and no counter is held against it |
| `throttled` | Back off further each time (1s, 2s, 3s… capped), and give up after `MAX_THROTTLED` |
| `noCursor` | The shard declined to start the swing. Backed off like a throttle, but counted |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

When nothing in reach is choppable but something is regrowing, the loop **idles until the soonest
one is due** rather than ending the run — sliced into `IDLE_POLL` sleeps, because one blocking sleep
of twenty minutes leaves the client unresponsive for all of them with no way to stop the script.

However the run ends, it makes boards and unloads one last time, so it finishes with boards on the
animal rather than logs in the pack.

### Before you paste it

- **Set `BOUNDS`.** The checked-in rectangle is a specific spot on UOAlive and means nothing
  anywhere else. Set it to `undefined` to roam.
- Stand inside that box. `stopReason()` runs before anything else, so starting outside it ends the
  run on cycle zero.
- **An axe in hand.** The run learns its graphic from what you are holding.
- **Your pack animals nearby**, if you want hauling. Only your own count — the search keeps the ones
  whose `isRenamable` is true.

### How to run it

```bash
npm run build
```

Paste `dist/lumberjack.js`. The opening line names how many logs are in the pack and which box it
will stay inside. Then correct `OUTCOME_TEXT` against what the journal actually says, since none of
the harvest phrasings have been confirmed here.

## What to set

Everything lives in [`config.ts`](config.ts). Values re-exported from
[`lib/timings.ts`](../lib/timings.ts) at the top of that file are shared with mining; to give
lumberjacking its own, delete it from the re-export list and declare it below.

The tables below cover what is worth changing. The rest of the re-exported list is plumbing that
should not need touching — `STEP_DELAY`, `WALK_DELAY`, `TARGET_TIMEOUT`, `IDLE_POLL`,
`EQUIP_ATTEMPTS` / `EQUIP_POLL` / `EQUIP_TIMEOUT`, `THROTTLE_BACKOFF` / `THROTTLE_BACKOFF_MAX`, and
the `SAVE_*` / `SAVING_TEXT` values that sit out a world save. They are commented in
`lib/timings.ts` where they are declared.

### Where to work

| Setting | What it is for |
| --- | --- |
| `BOUNDS` | **Set this first.** The box the character never steps outside, corners included. `undefined` roams. Trees outside it are still fair game as long as one can be reached from a tile inside it |
| `SCAN_RADIUS` | How far to look for a tree |
| `CHOP_RANGE` | 2. How close you have to be to hit one |

### Finding the trees

| Setting | What it is for |
| --- | --- |
| `TREE_GRAPHICS` | Empty. Trees are found by their tiledata *name*, so this stays empty unless this shard proves the name match wrong. Put a graphic in it if a harvestable tree is skipped |
| `NOT_TREE_GRAPHICS` | Also empty, and a seed only — a refusal learned on the shard goes to the run's memory, not back here. Put a graphic in it if a decorative static keeps being chopped at |
| `LOG_GRAPHICS` | The arts a log stack is drawn with. Hue is deliberately not part of the match: a shard with special woods hues its logs, and those still count, still convert and still need hauling |
| `REGROW_DELAY` | 25 minutes. The knob to turn if the script returns to a tree that is still bare |

### The tool

| Setting | What it is for |
| --- | --- |
| `AXE_NAME` | `'axe'`. The graphic is learned from the one you start holding |
| `SPARE_BAG_SERIAL` | Pin the bag the spares live in instead of discovering it |
| `CHOP_TIMEOUT` | 8s. A swing plays its animation before the result arrives, so this has to outlast the animation |

### Boards and hauling

| Setting | What it is for |
| --- | --- |
| `BOARD_GRAPHICS` | A seed only. The real board graphic is learned by diffing the pack across the first successful conversion, so a wrong guess costs nothing |
| `HAUL_BUFFER` | 120. The weight headroom at which it stops chopping and goes to make boards. Deliberately wider than the guards' `WEIGHT_BUFFER` (40), so hauling always gets its turn before the overweight stop fires |
| `PACK_ANIMAL_GRAPHICS` | Pack horse, pack llama, giant beetle. The search logs the body it finds, so an unusual animal can be added |
| `PACK_ANIMAL_SERIALS` | Pin the animals exactly and skip the search. Order does not matter — the haul walks to whichever is nearest first either way |
| `UNLOAD_RANGE` | 2. How close you have to be to move items onto the animal |
| `CONVERT_ATTEMPTS` | 3. Silent failures in a row before giving up on a hue. More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0 means hauling ordinary logs |
| `MAX_CONVERT_PASSES`, `CONVERT_DELAY`, `CONVERT_TIMEOUT`, `CONVERT_POLL`, `MOVE_DELAY` | Conversion and move pacing |

### Reading the journal

`OUTCOME_TEXT` maps journal phrases to the branches in the table above. Correct it against your
shard's journal after the first run — a phrase that never matches shows up as an `unknown` outcome,
which stops the run, rather than as a silent wrong turn. `UNSKILLED_TEXT` is checked by the board
conversion, which has no outcomes of its own.

### Stopping

| Setting | Default | What it is for |
| --- | --- | --- |
| `MAX_CYCLES` | | The backstop on the whole run |
| `MAX_UNKNOWN` | | Unreadable outcomes in a row before stopping |
| `MAX_THROTTLED` | | Refusals in a row before stopping |
| `MAX_STEPS` | | Steps spent walking to one tree before writing it off |
| `STALL_WARN` / `STALL_STOP` | | Cycles without a chop before it warns, then stops |
| `WEIGHT_BUFFER`, `PACK_LIMIT` | 40 / 120 | The overweight and item-cap guards |
| `HEARTBEAT_EVERY`, `LOG_EVERY`, `IDLE_LOG_EVERY` | | How often it says it is still alive |

## When it goes wrong

**The run ends on cycle zero saying `outside (…)-(…)`.** You are not inside `BOUNDS`. Either walk
into the box or change it.

**`no tree in range` in a forest.** Nothing matched the tiledata name and nothing is on cooldown.
Put a graphic into `TREE_GRAPHICS`.

**`unreadable outcome, check OUTCOME_TEXT`.** The expected case on a first run, since the phrasings
are guesses. Read the journal after a chop and correct them.

**`hauling freed nothing, carrying on until overweight`.** No animal found, or the one found will
take no more. Latched off after one failure so a missing animal costs one search rather than one per
cycle — check `PACK_ANIMAL_GRAPHICS`, or pin `PACK_ANIMAL_SERIALS`.

**It converts nothing and hauls plain logs.** A wood was written off after `CONVERT_ATTEMPTS` silent
passes. Hue 0 is *every* normal log, so this is worth checking: raise `CONVERT_ATTEMPTS` or confirm
the journal is not saying you are unskilled.

## Notes on the shard

Written against UOAlive, and **none of it confirmed by a lumberjacking run** — the notes marked as
confirmed come from mining runs that exercise the same shared code.

- One tree is several statics and only the trunk is harvestable, so a tile that runs out of wood is
  tracked per tile — a stump regrows, and a neighbour of the same art may still have wood.
- **A depleted tile is a cooldown, not a write-off.** The stump grows back, so *not enough wood*
  parks the tile until `REGROW_DELAY` has passed and the scan picks it up again on its own. Written
  off permanently, the script bans every tile it ever chopped and stops with *no tree in range*
  while standing in a forest.
- **"Target cannot be seen." is line of sight, and permanent.** The tile is already inside
  `CHOP_RANGE`, so neither walking closer nor waiting changes the answer — something is simply in
  the way. It is written off for good. Before it had its own `OUTCOME_TEXT` bucket it read as an
  unreadable outcome, was picked again by the very next scan, and five in a row ended the run.
- **What the failures mean is three different things, not one.** Out of wood → back in
  `REGROW_DELAY`. A walk that never closed → back in `UNREACHABLE_DELAY`, because what blocked the
  path is usually a player or a pet rather than the tree. Out of sight, out of shard-range, or an art
  that cannot be chopped → never again.
- **State that has to outlive the run lives on `globalThis`** ([`memory.ts`](memory.ts)): the blocked
  tiles and the arts the shard refuses. The QuickJS context persists between runs — the same fact the
  IIFE wrapping exists for — so a restart of the script inherits them, though a restart of the client
  does not. A 25-minute cooldown is longer than most runs, so without this every restart would swing
  at the tiles that had just gone empty and re-learn the forest from scratch. The store carries a
  version and is discarded rather than read if it does not match, so an edit to its shape cannot
  crash the first scan after a rebuild. `NOT_TREE_GRAPHICS` in `config.ts` is therefore a seed only.
- **The tiledata name over-reaches.** A live run matched `0xc9e`, named *o'hii tree*, and the shard
  answered **"You can't use an axe on that"** — the art is scenery. That answer is about the
  *graphic*, not the tile, so a refusal adds the graphic to the runtime ban list and every other copy
  of that art drops out of the scan at once, rather than being walked to and refused one tile at a
  time across the whole forest. The console names each distinct graphic the scan settles on, so the
  art that does work ends up in the log next to the art that does not.
- **`target.terrain` targets the *land* tile when the graphic argument is omitted, and the static
  standing on it when one is passed** — and the shard answers the land tile as mining rather than
  chopping. The chop therefore always passes the tree's graphic. (Mining goes the other way and names
  no tile at all; see [`src/mining`](../mining/README.md).)
- There is no pathfinding API — `player.walk`/`run` take one direction at a time. Walking to a tree
  is naive `Math.sign` stepping, and the direction is issued twice because the first packet in a new
  direction only turns the character. A tree that stops being reachable after `MAX_STEPS`, or that a
  step fails to close on at all, is written off like an exhausted one.
- **`BOUNDS` is enforced in one place.** `stepToward` is the only thing that ever moves the
  character, so that is where the box lives; `guards.ts` also stops the run if the character is
  outside one, which catches a teleporter, a boat, or a run started from the wrong place. A diagonal
  step that would leave the box falls back to whichever cardinal half stays inside, so the character
  slides along an edge instead of giving up — a box is mostly edge. Trees outside the box are still
  chopped when a legal standing tile is within `CHOP_RANGE` of them, and trees that no legal tile can
  reach are filtered out of the scan rather than picked, walked at, refused, and only written off
  `MAX_STEPS` later.
- Axes are two-handed and hatchets are one-handed, so the axe check reads
  `equippedItems.twoHanded ?? equippedItems.oneHanded` rather than mining's single hand layer.
- **Logs become boards by using the axe and targeting the log stack** — the same cursor the chop
  uses, and the inverse of smelting, where the *ore* is double-clicked and the forge is targeted.
  Stock RunUO answers with a sound and no message, so the conversion is read from a pack diff
  ([`lib/pack.ts`](../lib/pack.ts)) rather than the journal. That diff also *names* the board
  graphic: whatever gained amount as the logs left is a board, so `BOARD_GRAPHICS` is only a seed and
  a wrong guess corrects itself on the first conversion.
- Logs are matched by graphic alone, not graphic plus hue like ingots, because special woods are
  hued and still have to be counted and hauled.
- **A conversion is polled for, not slept through, and one silent attempt proves nothing.** The
  action throttle can hold a conversion past any pause worth taking, and a stale serial changes
  nothing either — both look exactly like a wood that cannot be worked. Reading the pack once after a
  fixed sleep and giving up on the hue there and then is what put ordinary logs on the pack animal:
  hue 0 is *every* normal log, so one hiccup disabled conversion for the whole run.
  [`boards.ts`](boards.ts) now polls for `CONVERT_TIMEOUT`, converts one stack per pass and rescans
  between them, and only gives up on a hue after `CONVERT_ATTEMPTS` silent tries in a row — or at
  once if the journal says outright that you are not skilled enough, which retrying cannot fix.
- Only boards and the logs of a given-up-on hue go onto the animal. A log still waiting its turn
  stays in the pack and the next haul retries it. The exception is a pack that is still over the haul
  threshold once the boards have gone: those logs travel as logs rather than ending the run
  overweight, and the haul logs a line saying so.
- Pack animals are found by body graphic within `SCAN_RADIUS`, keeping the ones whose `isRenamable`
  is true: only your own pets can be renamed, so that is what tells yours from a stranger's. Their
  packs come from `client.findItemOnLayer(serial, Layers.Backpack)`.
- **All of them get loaded, not just the nearest.** The haul walks the animals nearest-first and
  fills each in turn; one that stops accepting is full rather than broken, so what is left goes to
  the next. The leftover-logs fallback is asked only once every animal has had its turn — asking per
  animal would read a full first horse as the conversion having fallen behind, and would then try to
  push logs onto that same full horse.
- **Do not double-click the animal to find its pack if you can avoid it.** A giant beetle is
  rideable, so the double-click mounts you instead. [`haul.ts`](haul.ts) only falls back to it when
  the backpack layer comes back empty.
- Hauling fires at `HAUL_BUFFER` (120 stones of headroom), which is deliberately wider than the
  guards' `WEIGHT_BUFFER` (40), so there is room to work before the overweight stop. A haul that
  frees no weight latches hauling off for the rest of the run, or a missing animal would cost a fresh
  search every cycle.
- **A save freezes every part of a haul at once:** the conversion is silent, the animal takes
  nothing, and the weight does not move. Read as an ordinary result it would latch hauling off for
  the rest of the run — one unlucky ten seconds and every later load goes nowhere. `isSaving()` is
  checked before that conclusion is drawn.

### Known unverified

- **Everything about this script**, which has not been run. The harvest phrasing in `OUTCOME_TEXT`
  is stock RunUO wording as a hypothesis, and `LOG_GRAPHICS` assumes log stacks change graphic with
  size the way ore does. The pack log count is the silent fallback if the wording is wrong.
- `REGROW_DELAY`. 25 minutes is a guess at the shard's respawn timer. If the script comes back to a
  tile that is still bare, that constant is the one to raise; the console names every tile it parks
  and when it expects it back.
- The pack animal bodies in `PACK_ANIMAL_GRAPHICS` (`0x123` pack horse, `0x124` pack llama, `0x317`
  giant beetle) and whether `Layers.Backpack` resolves for someone else's mobile at all. The search
  logs how many animals it found and their names; `PACK_ANIMAL_SERIALS` pins an exact list if the
  guesses are wrong.
- Whether boards actually weigh less than logs here. If they do not, converting frees nothing and
  only the animals make a difference to how long a run lasts.
