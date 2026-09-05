# corpse — open your own corpse

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/open-corpse.js` | Finds the corpse that is named for you and double-clicks it, once |

## Why it exists

When you die your corpse lands under whatever killed you, wearing the same art as every other body
on the screen. Finding it by clicking is worst exactly when it matters — as a ghost, in a pile, with
the healer's gump in the way. This is one double-click issued at the right serial.

[`src/carving`](../carving/README.md) is the other corpse script and does the opposite: it walks a
field of *other* creatures' corpses with a knife. This one opens exactly one, moves nothing, and
exits.

## What it does

1. **Scans the world for `CORPSE_GRAPHIC`** and keeps what is within `SCAN_RANGE` — wider than
   reach, so a corpse you cannot touch can still be *reported*.
2. **Names them, nearest first.** The client's own name is taken where it has one; only the nameless
   ones are worth an `OPL_TIMEOUT` tooltip lookup, and at most `MAX_OPL_ASKS` of those.
3. **Picks yours.** `a corpse of <you>` with nothing else after the prefix is an **exact** match; a
   name that carries yours as a whole word some other way is a **loose** one. Exact beats loose,
   loose beats nearest, and distance breaks the ties — so two deaths in one spot resolve to the
   nearer of your two corpses.
4. **Falls back to the nearest** when nothing is named for you, saying so, and saying how many
   corpses would not tell it what they were.
5. **Checks the range last,** after the pick and never before it. A corpse at your feet must not be
   able to displace the one carrying your name — if yours is nine tiles out, the run stops and tells
   you that, rather than opening the mongbat you are standing on.
6. **Double-clicks it,** then polls its contents until the shard answers, and logs what it holds.

Nothing is moved and nothing is closed. Leaving the corpse window up is the whole point.

### Before you paste it

- **Stand within `OPEN_RANGE`.** Nothing here walks. Out of reach is a stop, with the distance in it.
- **The name match needs tooltip data.** A ghost cannot hover, so on some shards nothing comes back
  named and the run degrades to "the nearest one". It says so when it does — the count of corpses
  that would not answer is what tells that apart from a field of monster corpses.
- **It does not check whether you are dead.** Opening your corpse after a resurrection to get your
  gear back is the same job.
- **It does not need a backpack**, because it moves nothing.

### How to run it

```bash
npm run build
```

Then paste `dist/open-corpse.js` into the client's script editor.

```
corpse: looking for 'Fenwick' within 18 tiles - 0x2006 x4
corpse: 'a corpse of Fenwick' (0x40142a91) is yours, 1 tiles away - exact name match
corpse: 'a corpse of Fenwick' holds katana x1, leather tunic x1, gold x842
corpse: opened 0x40142a91 - 9 stacks, 856 items
```

Out of reach:

```
corpse: 'a corpse of Fenwick' (0x40142a91) is yours, 7 tiles away - exact name match
corpse: yours is 7 tiles away, and 'a corpse of a mongbat' in reach is not yours - walk to yours and run it again
```

## Config

`src/corpse/config.ts`.

| Setting | Default | What it does |
| --- | --- | --- |
| `CORPSE_GRAPHIC` | `0x2006` | Shared, in [`lib/arts.ts`](../lib/arts.ts) — `src/carving` reads the same one |
| `OPEN_RANGE` | `2` | The shard's reach. Further out is reported, not walked to |
| `SCAN_RANGE` | `18` | How far to look before concluding nothing of yours is about |
| `MAX_OPL_ASKS` | `8` | Tooltip lookups one run will pay for, spent nearest-first |
| `OPL_TIMEOUT` | `2000` | How long each of those waits |
| `OPEN_DELAY` | `800` | Pause after the double-click before the first contents read |
| `SETTLE_POLL` / `SETTLE_TIMEOUT` | `100` / `2000` | How often, and how long, to keep asking for contents |
| `LOG_ITEMS` | `40` | Stacks named in the log before it gives the totals instead |
| `CORPSE_PREFIX` | `'a corpse of '` | The wording an exact match is measured against |

## When it will not work

**`no corpses anywhere the client can see`** with a body plainly on the ground — `CORPSE_GRAPHIC` is
wrong for this shard. It is in `lib/arts.ts` and `src/carving` shares it, so check that script's
census line too.

**`nothing here is named for you (4 of 4 would not say what they are)`** — the client has no tooltip
data at all. Hover a corpse yourself and run it again, or accept the nearest.

**`would not say what it holds`** — the double-click went out and the window may well be up; the
shard just never answered with the contents. Usually no line of sight: two tiles by Chebyshev is not
two tiles the server will let you touch, and there is no line-of-sight call in this API to check it
with. Stand on the corpse and run it again.

## Notes on the shard

Written against UOAlive.

- **`client.findAllItemsOfType(0x2006, undefined, 'world')` is the whole of the scan**, and it does
  not care what is drawn on top of a corpse. That is the reason this beats clicking.
- **`0x2006` is deliberately not in `CONTAINER_GRAPHICS`,** so this opens the corpse with a bare
  `player.use` rather than through `openContainers` — see [`src/carving`](../carving/README.md).
- **A corpse that decayed inside the open is reported as gone, not as empty.** The serial is
  re-resolved after the wait, because an empty corpse and a vanished one otherwise read the same.

### Known unverified

- **The `a corpse of ` wording.** A shard that words it differently loses the exact tier, not the
  match — the loose whole-word test still finds your name in it.
- **`OPEN_RANGE` of 2.** The usual reach on a RunUO-family shard, not a measurement on this one.
- **Whether a ghost may double-click its own corpse at all.** Some shards refuse it. Nothing here
  reads the journal for a refusal wording, because a guessed phrase that never matches is worse than
  no phrase — it would land on the `would not say what it holds` stop instead.
