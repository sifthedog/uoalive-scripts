# boxes — emptying crafted wooden boxes

Builds two scripts:

| Script | What it does |
| --- | --- |
| `dist/boxes.js` | Opens every wooden box in the pack, keys on the floor, optionally sells the boxes |
| `dist/keys.js` | Drops the keys **already** in your pack. Touches nothing else |

## Why it exists

A vendor will not buy a container that still holds something, and a crafted wooden box arrives with
its key inside it. So the whole job is: open every box, take what is inside out, and only then say
`vendor sell`.

## What `dist/boxes.js` does

Each round:

1. **Find the boxes.** By graphic, falling back to the name. The search recurses, but a container's
   `contents` is `undefined` until it has been opened, so an unopened bag hides what is in it — a
   pack that reports no boxes gets one pass of double-clicks to rule that out.
2. **Peek at the tooltip.** RunUO renders `Contents: 3/125, 4 stones` into a container's OPL, and a
   count of zero is the server stating the box is already empty. That box is never opened. On a pile
   whose keys are mostly out already this is the difference between opening a hundred and opening two.
3. **Empty the rest.** Double-click, wait `OPEN_DELAY`, then move everything out: **keys to the
   floor, everything else into the pack** — an art the script does not recognise as a key ends up
   somewhere safe rather than on the ground. Moves are asynchronous, so the box is rescanned between
   passes; a pass that shifts nothing is a stall, not an empty box.
4. **Close the window** (`CLOSE_BOXES`).
5. **Sell**, if `SELL = true`. Then round again, because a large pile hits the 125-item container
   cap before it is all emptied and selling is what frees the room.

A box whose `contents` is still `undefined` after the double-click never opened — locked, most
likely. It keeps its key, it is excluded from the sale, and the closing line says how many there
were.

### Before you paste it

- Stand next to a **tinker or a carpenter** if `SELL = true`. The script says `vendor sell` out
  loud and offers to whoever is in earshot.
- Have room around your feet. Keys land on the nine tiles under and around you (`DROP_SPREAD`).
- Nothing needs to be equipped and you do not need to be off a mount.

### How to run it

```bash
npm run build
```

Then paste `dist/boxes.js` into the client's script editor. The console will say how many boxes it
found, then a line per box naming what came out of it and where it went (`LOG_EVERY_BOX`), then a
round summary, then a closing line with the totals and every graphic it took out of a box.

## What `dist/keys.js` does

The keys *already* in your backpack — the ones an earlier run put there before dropping worked —
thrown at your feet. The search recurses, so it also takes a key out of a bag or out of a box.

It reports every `LOG_EVERY_KEY` keys, because a pile of forty is otherwise one line, a long silence
and one more line, which reads exactly like a hung script. It gives up after `MAX_STUCK` keys in a
row refuse to drop, since each costs the full `DROP_TIMEOUT`.

## What to set

Everything lives in [`config.ts`](config.ts).

### Identifying things

| Setting | What it is for |
| --- | --- |
| `BOX_GRAPHICS` | The arts a wooden box is drawn with. `0x09aa` is what UOAlive uses; the `0x0e7d`/`0x0e7e` pair is the stock-art guess, kept for other shards |
| `BOX_NAME` | `'wooden box'`. Used two ways: as a **substring** when searching your pack, and as an **exact, case-insensitive** match against the vendor's gump. Naming the wrong thing in your pack costs a box that will not open; naming the wrong thing at the vendor sells something you meant to keep |
| `KEY_GRAPHICS` | The arts a key is drawn with. Matched alongside a `\bkey\b` test on the name, and the first key the client can name teaches the run the art for the rest |

Both are seeds. A box or key found by name gets its graphic logged, so the first run tells you what
to paste back in.

### What happens to the keys

| Setting | Default | What it is for |
| --- | --- | --- |
| `DROP_KEYS` | `true` | Off, the keys go into the pack instead — at which point the weight and pack-slot guards come back on (see below) |
| `DROP_SPREAD` | 9 tiles | Where the keys land, as offsets from where you stand, cycled one per key. `0/0/0` is your own tile. Cut it to a single `{ x: 0, y: 0, z: 0 }` to have everything land underfoot |
| `DROP_METHOD` | `'groundOffset'` | Which call drops an item here. `'auto'` tries each in turn and keeps whichever demonstrably moves the item |
| `DROP_TIMEOUT` / `DROP_POLL` | 3000 / 200 | How long a drop is polled for. Do not replace this with a flat sleep — see below |
| `MAX_STUCK` | 3 | Consecutive keys that will not drop before `keys.js` gives up |

### Selling

| Setting | Default | What it is for |
| --- | --- | --- |
| `SELL` | `false` | On, the run says `vendor sell` and offers the emptied boxes |
| `KEEP` | `0` | Leave this many boxes behind |
| `MAX_SELL_PASSES` | 10 | A sell gump lists a limited number of entries, so it reopens until nothing matches |
| `MAX_ROUNDS` | 20 | Empty, sell, go round again — a large pile hits the container cap before it is all emptied |
| `SELL_DELAY`, `SALE_TIMEOUT`, `SALE_POLL`, `GUMP_TIMEOUT` | | Sale pacing |

### Pace and noise

| Setting | Default | What it is for |
| --- | --- | --- |
| `PEEK_CONTENTS` | `true` | Read the tooltip before opening. Off, every box is opened the slow way |
| `CLOSE_BOXES` | `'perBox'` | `'perBox'` closes each box's own window as it is emptied. `'allGumps'` calls `client.closeAllGumps()` at the end — it definitely works, and it definitely also closes your paperdoll, character sheet and journal, because the client has no per-container close. `'never'` leaves them |
| `LOG_EVERY_BOX` | `true` | A line per box. Worth having on the first run — it is what puts the shard's real key graphic in the console. Turn it off for a pile of a hundred |
| `LOG_EVERY_KEY` | 5 | How often `keys.js` reports |
| `OPEN_DELAY`, `MOVE_DELAY`, `OPL_TIMEOUT`, `CLOSE_TIMEOUT` | | Timings. `MOVE_DELAY` is a pause between moves rather than a wait for one to land |
| `WEIGHT_BUFFER`, `PACK_LIMIT` | 40 / 120 | Only consulted when `DROP_KEYS` is off |
| `MAX_EMPTY_PASSES` | 5 | How many times a box may be rescanned while it is still shifting items |

## When it goes wrong

**`0 wooden boxes` next to a pack full of them.** `BOX_GRAPHICS` is wrong for this shard. The script
tries the name as a fallback and prints the graphic it learned; failing that it dumps the whole top
level of the pack and stops. The graphic that repeats as often as you have boxes is the one to
paste into `BOX_GRAPHICS`.

**`0 of 0 keys on the floor`.** Nothing that came out of a box was recognised as a key, so it all
went into the pack. The graphic it listed goes into `KEY_GRAPHICS`.

**`0 of 40 keys on the floor`.** They were recognised but no drop would land. The run will have said
which calls it tried; pin the winner as `DROP_METHOD`.

**`emptied 0` with a guard message.** With `DROP_KEYS = false` the weight and pack-slot guards are
live, and they stop the run before the first box. That is the fix they were given — see below.

**The vendor lists boxes but none of their serials match.** The run stops rather than selling by
name. Empty the boxes it could not open by hand and run again.

## Notes on the shard

Written against UOAlive.

- **A box is emptied wholesale** rather than having its key picked out, so the script never has to
  identify a key correctly — `KEY_GRAPHICS` only decides what hits the floor.
- **Only a box watched going empty is ever offered.** One whose `contents` is still `undefined`
  after the double-click never opened — locked, most likely. Once one has been skipped the sale
  matches the gump by serial rather than by name, and if none line up it stops: that is exactly the
  case where a name match would hand over the box that would not open, key and all.
- **Emptying a large pile hits the 125-item container cap, not the weight cap,** because a key taken
  out of a box adds one item to the *top level* while the total weight is unchanged. Throwing the
  keys on the floor is what avoids that.
- **`moveItemOnGroundOffset` offsets from *you*, not from the item, and 0/0/0 is your own tile.**
  The doubt was worth having, because an item inside a container reports the *slot* it occupies as
  its x/y, so an offset from the item would have landed nowhere.
- **A drop is polled for, not slept through.** The call is silent and returns an undocumented
  number, so the only proof is the item's container changing. Read back after a flat 700ms, a drop
  that had *worked* looked like one that had not — whereupon the recovery path moved the key "into
  the pack", picking it back up off the floor.
- **A container's tooltip says how much is in it, so most boxes never need opening.**
  [`peek.ts`](peek.ts) asks once and gives up on the property if the shard does not send it, rather
  than paying the OPL timeout per box forever. It is a count and not a list, so `undefined` always
  means "open it and see", never "empty".
- **UOAlive's wooden box is `0x09aa`,** not the `0x0e7d` of the stock art tables. It was identified
  at runtime off the name "Wooden Box", which is the whole reason the name fallback exists.
- **Guards copied from a crafting script are wrong in a script that empties things.** The inherited
  overweight and pack-full checks stopped a live run before the first of fifteen boxes: emptying a
  box onto the floor *frees* weight and a slot, so the overloaded character they fire on is exactly
  who the run would have relieved. They now apply only when `DROP_KEYS` is off.
- **A guard that stops a loop has to say so where it stops it.** The reason was kept for a stop
  message a `SELL = false` run never reached, so the console showed `15 wooden boxes` then
  `emptied 0` with no explanation for either.
- **What counts as a key decides what hits the floor, so it is matched two ways and fails safe.**
  `KEY_GRAPHICS` plus a `\bkey\b` test on the name — a whole word, because `key` inside `monkey`
  would put something on the ground that was never meant to go there. An art matching neither goes
  into the pack: a key you throw away by hand rather than a possession on the floor.
- **`client.sendSellRequest` returns whether the packet went out, not whether the vendor took
  anything,** and a vendor that refuses does so in silence. The boxes leaving the pack is the only
  proof, so `waitForSale` in [`lib/vendor.ts`](../lib/vendor.ts) polls the pack for the offered
  serials.

### Known unverified

- Whether the shard caps items per tile. `DROP_SPREAD` walks a key round the nine tiles under and
  around you rather than betting on one square, because the cost of being wrong is `DROP_TIMEOUT`
  per refused key.
- Whether a container's window is addressable as a gump under its own serial, which is what
  `CLOSE_BOXES = 'perBox'` assumes. If it is not, the lookup answers nothing and no window closes,
  which is the harmless direction.
