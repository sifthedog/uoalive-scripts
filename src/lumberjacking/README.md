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

At startup it opens a cursor to click your pack animals — one after another, ESC when done. ESC on
the first falls back to `PACK_ANIMAL_SERIALS`, and then to the body search. Then, every cycle:

1. **Check the stop conditions** — dead, outside `BOUNDS`, overweight, or the pack at its item cap.
2. **Equip an axe.** Axes are two-handed and hatchets one-handed, so it reads
   `equippedItems.twoHanded ?? equippedItems.oneHanded`.
3. **Haul, if the weight is over `HAUL_BUFFER`.** Boards are made first — only boards ever go on an
   animal — then every pack animal in range is walked to and filled, nearest first. Logs that would
   not convert stay in the pack and are tried again on the next haul.
4. **Scan for a tree** within `SCAN_RADIUS`, shortest walk first, skipping tiles the run has parked
   and trees there is no route to. If that box is dry, sweep again out to `ROAM_RADIUS`.
5. **Walk to it** if it is further than `CHOP_RANGE`. One routed step per cycle, planned over the
   walkability map in [`lib/grid.ts`](../lib/grid.ts) and confined to the box.
6. **Chop**, and branch on what the shard says.

Steps 1-3 and 6, along with the counters that end a run, are
[`lib/harvest.ts`](../lib/harvest.ts)'s `runHarvest` — the same loop `dist/mining.js` and
`dist/mine-here.js` run. Steps 4 and 5 are `createApproach` in [`lib/tiles.ts`](../lib/tiles.ts).
What this folder supplies is the wordings, the axe, the haul, and the outcomes in the table below.

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

When nothing within `ROAM_RADIUS` is choppable but something is regrowing, the loop **idles until the
soonest one is due** rather than ending the run — sliced into `IDLE_POLL` sleeps, because one blocking sleep of
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

## Trouble

The shard runs encounters that spawn monsters at anyone macroing AFK. Every cycle — and every slice
of an idle wait, which is where a run stands still longest — the loop checks four things: a hostile
mobile within `THREAT_RANGE`, your health going down, your nearest pack animal's health going down,
and any wording in `ATTACK_TEXT`. Any one of them opens an episode: it says `guards`, up to
`GUARD_CALLS` times, one call per `GUARD_CALL_DELAY`, and goes on chopping. The count resets when a
check comes back clear, so something that comes back gets a fresh set of calls.

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
[`lib/timings.ts`](../lib/timings.ts) at the top of that file are shared with mining; to give
lumberjacking its own, delete it from the re-export list and declare it below.

### Where to work

| Setting | What it is for |
| --- | --- |
| `BOUNDS` | **Set this first.** The box the character never steps outside, corners included. `undefined` roams. Trees outside it are still fair game as long as one can be reached from a tile inside it |
| `SCAN_RADIUS` | 12. How far to look for a tree on an ordinary cycle |
| `ROAM_RADIUS` | 24. Swept only when the `SCAN_RADIUS` box is dry, so its terrain reads are paid on the cycle that would otherwise stand still |
| `CHOP_RANGE` | 2. How close you have to be to hit one |
| `RESET_MEMORY` | `false`. Turn it on for one run to drop the blocked tiles and banned arts a previous one left on `globalThis` |
| `ROUTE_RADIUS`, `MAX_ROUTE_NODES`, `MAX_ROUTE_CELLS` | The route flood's box, its node cap and its terrain cache. `ROUTE_RADIUS` has to cover `ROAM_RADIUS` or `stepsTo` clips the far trees back out |
| `MAX_CLIMB`, `PLAYER_HEIGHT`, `STEP_HEADROOM` | What a step may climb, and how far above and below a standing spot a solid art still counts as being in the way |
| `SURVEY_ARTS` | 15. Arts named when a sweep comes up empty, commonest first |

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
| `CHOP_TARGET_TIMEOUT`, `CHOP_TARGET_POLL` | 4s / 100ms. The cursor is waited for by polling two signals, so this is longer than the shared `TARGET_TIMEOUT` |
| `CHOP_PROMPT_TEXT` | The wording the shard opens the cursor with. Unverified — correct it against the journal. Read only so a cursor `target.open` missed is not mistaken for a refusal |

### Boards and hauling

| Setting | What it is for |
| --- | --- |
| `BOARD_GRAPHICS` | A seed only. The real board graphic is learned by diffing the pack across the first conversion |
| `HAUL_BUFFER` | 120. The weight headroom at which it stops chopping and goes to make boards. Deliberately wider than the guards' `WEIGHT_BUFFER` (40), so hauling always gets its turn first |
| `PACK_ANIMAL_GRAPHICS` | Pack horse, pack llama, giant beetle. The search logs the body it finds |
| `PACK_ANIMAL_SERIALS` | Pin the animals exactly and skip the search. Order does not matter, and the cursor overrides it for the run |
| `PICK_PACK_ANIMALS` | On by default: a cursor at startup to click your animals, ESC to fall back. A picked list is pinned |
| `MAX_PICKS` | 8. A backstop on the cursor only — the selection ends when you press ESC |
| `OPL_TIMEOUT` | 2s. How long to wait for the tooltip that names a pick |
| `UNLOAD_RANGE` | 2. How close you have to be to move items onto the animal |
| `CONVERT_ATTEMPTS` | 3. Silent failures in a row before giving up on a hue. A save, a throttle and a cursor that never opened are all excluded, so reaching this means the wood really did not work — raising it is rarely the fix |
| `MAX_CONVERT_PASSES`, `CONVERT_DELAY`, `CONVERT_TIMEOUT`, `CONVERT_POLL`, `MOVE_DELAY` | Conversion and move pacing |

### Reading the journal

`OUTCOME_TEXT` maps journal phrases to the branches above. Correct it against your shard's journal
after the first run — a phrase that never matches shows up as an `unknown` outcome, which stops the
run, rather than as a silent wrong turn. `UNSKILLED_TEXT` is checked by the board conversion, which
has no outcomes of its own.

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
| `MAX_TREE_STEPS` | 40 | Steps spent walking to one tree before writing it off. Has to reach across `ROAM_RADIUS`; the shared `MAX_STEPS` of 20 is the haul's |
| `STALL_WARN` / `STALL_STOP` | | Cycles without a chop before it warns, then stops |
| `WEIGHT_BUFFER`, `PACK_LIMIT` | 40 / 120 | The overweight and item-cap guards |
| `HEARTBEAT_EVERY`, `LOG_EVERY`, `IDLE_LOG_EVERY` | | How often it says it is still alive |

## When it goes wrong

**The run ends on cycle zero saying `outside (…)-(…)`.** You are not inside `BOUNDS`.

**`no tree in range` in a forest.** Nothing matched the tiledata name and nothing is on cooldown. The
run prints what the walkability map and the survey saw before it exits; put a graphic that reads
`MATCHES` into `TREE_GRAPHICS`.

**It chops a tree out, then stands still counting down `Nm to go`.** Everything within `ROAM_RADIUS`
is parked. The line above it names which kind:

- *regrowing* — the stand really is stumps. `ROAM_RADIUS` is too small for the forest, or
  `REGROW_DELAY` is longer than the shard's own timer.
- *with no route* — the trees are there and the walk cannot reach them. Check `BOUNDS` is not
  penning the character in, and `lib/flags.ts` against the `grid:` line, which says so outright when
  the tile under your feet reads as impassable.
- *written off for good* — line-of-sight and unchoppable-art bans, which live on `globalThis` and
  outlive a restart of the script. Run once with `RESET_MEMORY = true` to drop them.

**`unreadable outcome, check OUTCOME_TEXT`.** The expected case on a first run, since the phrasings
are guesses. Read the journal after a chop and correct them.

**`no target cursor (n/20), backing off`.** The shard declined to start the swing and said nothing
about why. A few is ordinary; a run of them with an axe in hand means the shard is refusing in a
wording `THROTTLED_TEXT` does not have, or that `CHOP_PROMPT_TEXT` has the wrong wording and the
cursor is being missed rather than never opened. The line before them names what is in the hand.

A run of them starting after several good chops used to be this file's own fault: the swing opened
with an unconditional `target.cancel()`, which left `target.open` false for the cursor that
followed. It now cancels only when there is a cursor to cancel, the same fix
[`mining/dig.ts`](../mining/dig.ts) carries.

**`no pack animal found, carrying on until overweight`.** Latched off after one failed search, so a
missing animal costs one search rather than one per cycle — click the animals at startup, check
`PACK_ANIMAL_GRAPHICS`, or pin `PACK_ANIMAL_SERIALS`. An animal that is merely full does not latch
it: it is walked to again next cycle.

**`N logs would not convert, keeping them in the pack`.** The wood is never hauled as logs, so the
weight stays and the run ends on the stall watch if it never converts. Check the journal is not
saying you are unskilled, and confirm `BOARD_GRAPHICS` against the shard before raising
`CONVERT_ATTEMPTS`. Two faults that used to cause it, both fixed: the conversion opened with an
unconditional `target.cancel()` that swallowed its own cursor, and `THROTTLED_TEXT` was never passed
to the converter, so the shard saying it was busy read as a verdict on the wood.

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
  issued twice because the first packet in a new direction only turns the character. The route is
  planned over `getTerrainList`'s flags in [`lib/grid.ts`](../lib/grid.ts), the same map mining uses:
  **trees are the impassable statics a walk to a tree has to get around**, so a straight `Math.sign`
  line shuffled into one until it was written off for `UNREACHABLE_DELAY`, a tile at a time, until
  the whole box was on a cooldown and the character stood still.
- **`BOUNDS` is enforced in one place.** `stepToward` is the only thing that ever moves the character;
  `guards.ts` also stops the run if the character is outside the box, which catches a teleporter, a
  boat, or a run started from the wrong place. A diagonal step that would leave the box falls back to
  whichever cardinal half stays inside, since a box is mostly edge. The box is also passed to the
  route flood, so a plan can never leave it and then be refused a step at a time. Trees with no route
  are filtered out of the scan rather than picked, walked at, refused and written off later.
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
- **Only boards go onto the animal, never logs.** A log that leaves as a log never comes back as a
  board, so a wood given up on stays in the pack and every `makeBoards` reconsiders it — the verdict
  is a backstop for one pass, not for the run. Mining keeps the converter's progress gate, which is
  why `retry` takes a `force`.
- Pack animals are found by body graphic, keeping the ones whose `isRenamable` is true — only your
  own pets can be renamed. Their packs come from `client.findItemOnLayer(serial, Layers.Backpack)`.
- **All of them get loaded, not just the nearest.** One that stops accepting is full rather than
  broken, so what is left goes to the next.
- **Do not double-click the animal to find its pack if you can avoid it.** A giant beetle is
  rideable, so the double-click mounts you. [`haul.ts`](haul.ts) only falls back to it when the
  backpack layer comes back empty.
- **A save freezes every part of a haul at once:** the conversion is silent, the animal takes nothing,
  and the weight does not move. Read as an ordinary result it would latch hauling off for the rest of
  the run, so `isSaving()` is checked before that conclusion is drawn.
- **A save freezes the walking too.** No step moves you, which both `createApproach` and
  [`lib/entity.ts`](../lib/entity.ts)'s `approach` would otherwise read as a wall — writing off every
  tree the run was walking to for `UNREACHABLE_DELAY`, and abandoning the walk to the animal. Both
  take `isSaving` so a step spent during a save ends neither.

### Known unverified

- **Everything the guard call rests on.** Whether `guards` is the phrase this shard takes, whether
  guards answer monsters here at all, and the wordings in `NO_GUARDS_TEXT`, `GUARD_ZONE_TEXT` and
  `UNGUARDED_TEXT` — all stock RunUO guesses.
- **`HOSTILE_NOTORIETY`**: whether this shard's encounter spawns come up gray or red. If they are
  gray they share a notoriety with every cat and crow, so the call waits for blood — put them in
  `CALL_ON_SIGHT_NOTORIETY` only if a gray in sight is worth shouting at here.
- Whether `client.selectEntity` disturbs the client's current target, and so whether the watch can
  cost a swing its cursor the way `target.cancel()` was found to.
- **Everything about this script**, which has not been run. `OUTCOME_TEXT` is stock RunUO wording as a
  hypothesis, and `LOG_GRAPHICS` assumes log stacks change graphic with size the way ore does.
- `REGROW_DELAY`. 25 minutes is a guess at the shard's respawn timer.
- The pack animal bodies in `PACK_ANIMAL_GRAPHICS`, and whether `Layers.Backpack` resolves for
  someone else's mobile at all. `PACK_ANIMAL_SERIALS` pins an exact list if the guesses are wrong.
- Whether boards actually weigh less than logs here. If they do not, converting frees nothing.
