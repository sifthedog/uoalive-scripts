# carving — a butcher knife on every corpse in reach

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/carve.js` | Carves every corpse within reach and moves the feathers into your backpack |

## What it does

Per cycle:

1. **Check the stop conditions** — dead, overweight, pack full.
2. **Sit out a world save** if one is running.
3. **Prove a knife exists** — in hand, in the pack, or in a bag in the pack. It is used out of the
   pack and never equipped.
4. **Empty a carved corpse** if one in reach still holds anything in `TAKE_GRAPHICS`: open it, move
   the stacks, poll until they leave.
5. **Otherwise carve** the nearest corpse in reach that has not been dealt with — double-click the
   knife, answer the cursor with the corpse, read the journal.
6. **Nothing in reach** → heartbeat and poll again. This is the script waiting for you to kill
   something, so it counts neither as a stall nor against the cycle backstop — a run left watching an
   empty field does not end on its own.

Outcomes and what each one costs the corpse:

| Outcome | What happens |
| --- | --- |
| `carved` | Counted, and the corpse is not carved again |
| `nothingLeft` | Not carved again, but still opened once — someone else's carve leaves the feathers behind |
| `notCarvable` | Never carved and never opened again |
| `tooFar` / `notSeen` | Set aside for `BLOCKED_DELAY` |
| `throttled` / `saving` | Backed off and retried, on the shared loop's budgets |

### Before you paste it

- **Nothing walks.** Corpses further out than `CARVE_RANGE` are left where they fell — step over to
  them and the next cycle takes them.
- **A knife in your pack is enough.** The weapon in your hand is never put down, because whoever runs
  this is in the middle of a fight.
- **Trouble is not watched for.** The other scripts call the guards at a hostile in sight; this one
  does not, since the thing that made the corpse is usually still standing there.
- Every corpse is carved, human ones included — the shard's refusal is what teaches it otherwise, and
  it only has to be told once per corpse.

### How to run it

```bash
npm run build
```

Then paste `dist/carve.js` into the client's script editor. The first line is a census — how many
corpses the client can see in the whole world — so a wrong `CORPSE_GRAPHIC` shows up immediately
rather than as an afternoon of silence.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `CORPSE_GRAPHIC` | `0x2006` | Every corpse in the game is this art; what died is in the hue. Shared, in [`lib/arts.ts`](../lib/arts.ts) — [`src/corpse`](../corpse/README.md) reads the same one |
| `KNIFE_GRAPHICS` | butcher knife, cleaver, dagger, skinning knife | Seeds — the real art is learned off the first one found |
| `KNIFE_NAME` | `knife` | The name fallback, for a shard whose art is not in the list |
| `SPARE_BAG_SERIAL` | `undefined` | Pin the bag the knives are in instead of discovering it |
| `TAKE_GRAPHICS` | `0x1bd1` | What gets moved out of a carved corpse. Hides, ribs and scales are a line each |
| `LOOT_CORPSES` | `true` | Off if this shard puts the feathers straight in your pack — each open costs a cycle |
| `CARVE_RANGE` | `2` | The shard's reach. Raising it past what the server allows just makes every carve fail |
| `CARVE_TIMEOUT` | `3000` | How long to wait for the shard to say what happened |
| `WATCH_POLL` | `400` | Between scans that found nothing in reach |
| `OPEN_DELAY` / `MOVE_DELAY` | `800` / `250` | After opening a corpse, and between one move and the next |
| `SETTLE_TIMEOUT` / `SETTLE_POLL` | `2000` / `100` | How long to wait for the stacks to leave the corpse |
| `BLOCKED_DELAY` | `60_000` | How long a corpse that was out of reach, out of sight, or that kept its feathers is left alone |
| `MAX_CYCLES` | `100_000` | Carves and loots before the run stops. Idle polls do not count |
| `PRUNE_EVERY` | `50` | Idle passes between sweeps of the memory for corpses that have decayed |
| `WEIGHT_BUFFER` | `20` | Stones kept clear of the limit, so the stop lands before the shard refuses |
| `OUTCOME_TEXT` | guesses | The journal phrases. Correct these first when anything goes wrong |

## When it goes wrong

**`0x2006 x0 in the world`** with corpses plainly on the ground — `CORPSE_GRAPHIC` is wrong for this
shard. Hover one and read its art.

**`unreadable outcome (n/5), check OUTCOME_TEXT`** — the shard words carving differently. Carve one
by hand, read what it says, and put that wording in the right bucket.

**`no butcher knife`** — said only after `MAX_NO_TOOL` cycles found none, since the search reads the
pack and a read that threw is not a pack with no knife in it. The pack line printed just above lists
what the pack actually holds. If the knives are in a bag inside a bag, pin it as `SPARE_BAG_SERIAL`.

**`n corpses about, nearest N tiles away`** — they are further out than `CARVE_RANGE`. Said once per
run, because a field of out-of-reach corpses logs identically to an empty one. Nothing here walks.

**`still here - watching`** forever with a fresh kill next to you — the corpse is already in the
run's memory. It survives a re-paste on purpose; restart the client to clear it.

**`no target cursor (n/20)`** — the shard is declining to start the action. Usually a knife the
server does not consider a carving tool, or a corpse that has already decayed.

## Notes on the shard

Written against UOAlive.

- **`client.findAllItemsOfType(0x2006, undefined, 'world')` is the whole of the corpse scan.** There
  is no unfiltered item enumeration in this API — every item search is keyed on a graphic.
- **No container filter, unlike [`sweep`](../sweep/floor.ts).** A corpse is never inside anything,
  so the parent serial decides nothing here.
- **A corpse's `contents` is `undefined` until it has been opened**, which is why a corpse is only
  ever opened after it has been carved: asking costs a cycle whatever the answer.
- **`0x2006` is deliberately not in `CONTAINER_GRAPHICS`.** Adding it would have `openContainers` —
  which the tool search calls while hunting the pack for a spare — start double-clicking corpses in
  every other script.
- **The memory lives on `globalThis`,** so re-pasting the script does not re-carve the field. It is
  pruned on the idle path: a serial the client can no longer resolve has decayed.

### Known unverified

- **Every phrase in `OUTCOME_TEXT`.** RunUO-family guesses, none of them measured on this shard. A
  phrase that never matches shows up as an unreadable outcome, not as a silent wrong turn.
- **`CORPSE_GRAPHIC` of `0x2006`.** The stock corpse art. The startup census is there to catch a
  shard where it is not.
- **Whether feathers land in the pack or stay on the corpse.** Both are handled — the carve counts
  either way, and the loot pass writes off a corpse that turns out to hold nothing.
- **`CARVE_RANGE` of 2.** The usual reach on a RunUO-family shard, not a measurement on this one.
