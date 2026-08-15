# lumberjacking — chop trees, make boards, load the animals

Builds one script: `dist/lumberjack.js`.

> **This one has never been run.** `client.getTerrainList` and `client.getStatic` are used for the
> first time here, and most of `OUTCOME_TEXT` is stock RunUO wording taken as a hypothesis. Two
> phrases have since been confirmed from live *mining* runs — `notTree` and `notSeen`. Wrong phrasing
> shows up as `unknown` outcomes, which stop the run after `MAX_UNKNOWN` rather than flailing.

## Why it exists

The pack fills with logs that weigh more than the boards they become, so the script does the whole
cycle: work a patch of forest, turn the logs into boards when the weight climbs, and put the boards
on your pack animals.

Unlike mining, it stays inside a **bounds box** — a forest is a place you work, and roaming out of it
is how a script ends up in a town or in the water.

## What it does

Every cycle:

1. **Check the stop conditions** — dead, outside `BOUNDS`, overweight, or the pack at its item cap.
2. **Equip an axe.** Axes are two-handed and hatchets one-handed, so it reads
   `equippedItems.twoHanded ?? equippedItems.oneHanded`.
3. **Haul, if the weight is over `HAUL_BUFFER`.** Boards are made first — an unconvertible wood still
   gets hauled, but a convertible one travels lighter — then every pack animal in range is walked to
   and filled, nearest first.
4. **Scan for a tree** within `SCAN_RADIUS`, nearest first, skipping tiles the run has parked and
   trees no legal standing tile could reach.
5. **Walk to it** if it is further than `CHOP_RANGE`. One naive `Math.sign` step per cycle, and a
   step that would leave the box falls back to whichever cardinal half stays inside.
6. **Chop**, and branch on what the shard says.

| Outcome | What the loop does |
| --- | --- |
| `chopped` | Count it and carry on |
| `empty` | Out of wood. Park that tile for `REGROW_DELAY` — a stump grows back |
| `notTree` | Ban the whole graphic. The tiledata over-reaches, and one refusal drops every copy of that art out of the scan at once |
| `tooFar` | The shard disagreeing about the range. Set the tile aside |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `wornOut` | The axe broke; the next cycle equips a spare |
| `saving` | The shard is writing its world file. Sit it out; no counter is held against it |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | No cursor, and the journal explained nothing. Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

When nothing in reach is choppable but something is regrowing, the loop **idles until the soonest one
is due** rather than ending the run — sliced into `IDLE_POLL` sleeps, because one blocking sleep of
twenty minutes leaves the client unresponsive with no way to stop the script.

However the run ends, it makes boards and unloads one last time.

### Before you paste it

- **Set `BOUNDS`.** The checked-in rectangle is a specific spot on UOAlive and means nothing anywhere
  else. Set it to `undefined` to roam.
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
will stay inside. Then correct `OUTCOME_TEXT` against what the journal actually says.

## What to set

Everything lives in [`config.ts`](config.ts). Values re-exported from
[`lib/timings.ts`](../lib/timings.ts) at the top of that file are shared with mining; to give
lumberjacking its own, delete it from the re-export list and declare it below.

### Where to work

| Setting | What it is for |
| --- | --- |
| `BOUNDS` | **Set this first.** The box the character never steps outside, corners included. `undefined` roams. Trees outside it are still fair game as long as one can be reached from a tile inside it |
| `SCAN_RADIUS` | How far to look for a tree |
| `CHOP_RANGE` | 2. How close you have to be to hit one |

### Finding the trees

| Setting | What it is for |
| --- | --- |
| `TREE_GRAPHICS` | Empty. Trees are found by their tiledata *name*, so this stays empty unless this shard proves the name match wrong |
| `NOT_TREE_GRAPHICS` | Also empty, and a seed only — a refusal learned on the shard goes to the run's memory, not back here |
| `LOG_GRAPHICS` | The arts a log stack is drawn with. Hue is deliberately not part of the match: a shard with special woods hues its logs, and those still count |
| `REGROW_DELAY` | 25 minutes. The knob to turn if the script returns to a tree that is still bare |

### The tool

| Setting | What it is for |
| --- | --- |
| `AXE_NAME` | `'axe'`. The graphic is learned from the one you start holding |
| `SPARE_BAG_SERIAL` | Pin the bag the spares live in instead of discovering it |
| `CHOP_TIMEOUT` | 8s. A swing plays its animation before the result arrives |

### Boards and hauling

| Setting | What it is for |
| --- | --- |
| `BOARD_GRAPHICS` | A seed only. The real board graphic is learned by diffing the pack across the first conversion |
| `HAUL_BUFFER` | 120. The weight headroom at which it stops chopping and goes to make boards. Deliberately wider than the guards' `WEIGHT_BUFFER` (40), so hauling always gets its turn first |
| `PACK_ANIMAL_GRAPHICS` | Pack horse, pack llama, giant beetle. The search logs the body it finds |
| `PACK_ANIMAL_SERIALS` | Pin the animals exactly and skip the search. Order does not matter |
| `UNLOAD_RANGE` | 2. How close you have to be to move items onto the animal |
| `CONVERT_ATTEMPTS` | 3. Silent failures in a row before giving up on a hue. More than one, because a throttled or stale attempt also looks silent, and giving up on hue 0 means hauling ordinary logs |
| `MAX_CONVERT_PASSES`, `CONVERT_DELAY`, `CONVERT_TIMEOUT`, `CONVERT_POLL`, `MOVE_DELAY` | Conversion and move pacing |

### Reading the journal

`OUTCOME_TEXT` maps journal phrases to the branches above. Correct it against your shard's journal
after the first run — a phrase that never matches shows up as an `unknown` outcome, which stops the
run, rather than as a silent wrong turn. `UNSKILLED_TEXT` is checked by the board conversion, which
has no outcomes of its own.

### Stopping

| Setting | Default | What it is for |
| --- | --- | --- |
| `MAX_CYCLES` | | The backstop on the whole run |
| `MAX_UNKNOWN` | | Unreadable outcomes in a row before stopping |
| `MAX_THROTTLED` | | Refusals in a row before stopping |
| `MAX_NO_CURSOR` | 20 | Swings the shard opened no cursor for, in a row, before stopping |
| `MAX_STEPS` | | Steps spent walking to one tree before writing it off |
| `STALL_WARN` / `STALL_STOP` | | Cycles without a chop before it warns, then stops |
| `WEIGHT_BUFFER`, `PACK_LIMIT` | 40 / 120 | The overweight and item-cap guards |
| `HEARTBEAT_EVERY`, `LOG_EVERY`, `IDLE_LOG_EVERY` | | How often it says it is still alive |

## When it goes wrong

**The run ends on cycle zero saying `outside (…)-(…)`.** You are not inside `BOUNDS`.

**`no tree in range` in a forest.** Nothing matched the tiledata name and nothing is on cooldown. Put
a graphic into `TREE_GRAPHICS`.

**`unreadable outcome, check OUTCOME_TEXT`.** The expected case on a first run, since the phrasings
are guesses. Read the journal after a chop and correct them.

**`no target cursor (n/20), backing off`.** The shard declined to start the swing and said nothing
about why. A few is ordinary; a run of them with an axe in hand means the shard is refusing in a
wording `THROTTLED_TEXT` does not have. The line before them names what is in the hand and whether a
cursor was up.

**`hauling freed nothing, carrying on until overweight`.** No animal found, or the one found will
take no more. Latched off after one failure so a missing animal costs one search rather than one per
cycle — check `PACK_ANIMAL_GRAPHICS`, or pin `PACK_ANIMAL_SERIALS`.

**It converts nothing and hauls plain logs.** A wood was written off after `CONVERT_ATTEMPTS` silent
passes. Hue 0 is *every* normal log, so this is worth checking: raise `CONVERT_ATTEMPTS` or confirm
the journal is not saying you are unskilled.

## Notes on the shard

Written against UOAlive, and **none of it confirmed by a lumberjacking run** — what is marked as
confirmed comes from mining runs that exercise the same shared code.

- One tree is several statics and only the trunk is harvestable, so a tile that runs out of wood is
  tracked per tile — a stump regrows, and a neighbour of the same art may still have wood.
- **A depleted tile is a cooldown, not a write-off.** Written off permanently, the script bans every
  tile it ever chopped and stops with *no tree in range* while standing in a forest.
- **"Target cannot be seen." is line of sight, and permanent.** The tile is already inside
  `CHOP_RANGE`, so nothing changes the answer. Before it had its own bucket it read as an unreadable
  outcome, was picked again by the very next scan, and five in a row ended the run.
- **Three failures, three meanings.** Out of wood → back in `REGROW_DELAY`. A walk that never closed
  → back in `UNREACHABLE_DELAY`, because what blocked the path is usually a player or a pet. Out of
  sight, out of shard-range, or an art that cannot be chopped → never again.
- **State that has to outlive the run lives on `globalThis`** ([`memory.ts`](memory.ts)). The QuickJS
  context persists between runs — the same fact the IIFE wrapping exists for — so a restart of the
  script inherits the blocked tiles, though a restart of the client does not. Without it every
  restart would swing at the tiles that had just gone empty. The store carries a version and is
  discarded rather than read if it does not match. `NOT_TREE_GRAPHICS` is therefore a seed only.
- **The tiledata name over-reaches.** A live run matched `0xc9e`, named *o'hii tree*, and the shard
  answered **"You can't use an axe on that"** — the art is scenery. That answer is about the
  *graphic*, so the ban drops every other copy of that art out of the scan at once, rather than one
  tile at a time across the whole forest.
- **`target.terrain` targets the *land* tile when the graphic argument is omitted**, and the shard
  answers the land tile as mining rather than chopping. The chop therefore always passes the tree's
  graphic. (Mining goes the other way and names no tile at all.)
- There is no pathfinding API — `player.walk`/`run` take one direction at a time. The direction is
  issued twice because the first packet in a new direction only turns the character.
- **`BOUNDS` is enforced in one place.** `stepToward` is the only thing that ever moves the character;
  `guards.ts` also stops the run if the character is outside the box, which catches a teleporter, a
  boat, or a run started from the wrong place. A diagonal step that would leave the box falls back to
  whichever cardinal half stays inside, since a box is mostly edge. Trees no legal tile can reach are
  filtered out of the scan rather than picked, walked at, refused and written off `MAX_STEPS` later.
- **Logs become boards by using the axe and targeting the log stack** — the inverse of smelting.
  Stock RunUO answers with a sound and no message, so the conversion is read from a pack diff
  ([`lib/pack.ts`](../lib/pack.ts)). That diff also *names* the board graphic, so `BOARD_GRAPHICS` is
  only a seed and a wrong guess corrects itself on the first conversion.
- Logs are matched by graphic alone, not graphic plus hue like ingots, because special woods are hued
  and still have to be counted and hauled.
- **A conversion is polled for, not slept through, and one silent attempt proves nothing.** The
  action throttle can hold a conversion past any pause worth taking, and a stale serial changes
  nothing either — both look exactly like a wood that cannot be worked. Giving up there and then is
  what put ordinary logs on the pack animal: hue 0 is *every* normal log, so one hiccup disabled
  conversion for the whole run.
- Only boards and the logs of a given-up-on hue go onto the animal; a log still waiting its turn
  stays in the pack. The exception is a pack still over the haul threshold once the boards have gone:
  those logs travel as logs rather than ending the run overweight.
- Pack animals are found by body graphic, keeping the ones whose `isRenamable` is true — only your
  own pets can be renamed. Their packs come from `client.findItemOnLayer(serial, Layers.Backpack)`.
- **All of them get loaded, not just the nearest.** One that stops accepting is full rather than
  broken, so what is left goes to the next. The leftover-logs fallback is asked only once every animal
  has had its turn — asking per animal would read a full first horse as the conversion falling behind.
- **Do not double-click the animal to find its pack if you can avoid it.** A giant beetle is
  rideable, so the double-click mounts you. [`haul.ts`](haul.ts) only falls back to it when the
  backpack layer comes back empty.
- **A save freezes every part of a haul at once:** the conversion is silent, the animal takes nothing,
  and the weight does not move. Read as an ordinary result it would latch hauling off for the rest of
  the run, so `isSaving()` is checked before that conclusion is drawn.

### Known unverified

- **Everything about this script**, which has not been run. `OUTCOME_TEXT` is stock RunUO wording as a
  hypothesis, and `LOG_GRAPHICS` assumes log stacks change graphic with size the way ore does.
- `REGROW_DELAY`. 25 minutes is a guess at the shard's respawn timer.
- The pack animal bodies in `PACK_ANIMAL_GRAPHICS`, and whether `Layers.Backpack` resolves for
  someone else's mobile at all. `PACK_ANIMAL_SERIALS` pins an exact list if the guesses are wrong.
- Whether boards actually weigh less than logs here. If they do not, converting frees nothing.
