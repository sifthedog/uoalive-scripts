# selling — sell every stack of one item

Builds two scripts:

| Script | What it does |
| --- | --- |
| `dist/sell.js` | Target an item, sell every stack of it, stop |
| `dist/sell-watch.js` | Target an item, then keep selling it in batches as the pack fills |

## Why it exists

A vendor's sell gump lists whatever it will buy, and clearing forty stacks of the same thing out of
it by hand is forty clicks — repeated, because the gump only lists so many entries at a time. Point
at one item and the script sells every stack of it in your pack.

`sell-watch` is the same sale on a timer, for when you are producing the item rather than clearing
it out: stand at the vendor and it sells a batch every time enough has piled up.

## What `sell` does

1. **Asks you to target an item.** The serial comes off `target.query()`'s return value, and the
   name off the tooltip — an item you have never hovered has no name until the client has OPL data
   for it.
2. **Says `vendor sell`** and matches the gump's entries against the name — exactly and
   case-insensitively, never as a substring, so targeting a `wooden box` does not sweep up
   `small wooden box`.
3. **Sends the sell request** and then watches the goods leave the pack, because that is the only
   proof the vendor took anything.
4. **Reopens the gump** only if matching items are genuinely still in the pack — a sell gump lists a
   limited number of entries, so a pile too big to list at once needs another pass.

There is a hoisting step (`HOIST_FROM_BAGS`) that moves matching items out of bags before the sale.
It is **off**, because this shard's vendors read a bag as readily as the top of the pack — see
*Notes on the shard*. Turn it on only if yours does not.

## What `sell-watch` adds

1. **Targets once**, then loops.
2. **Counts the pack every `WATCH_POLL`, silently.** Counting reads the pack; it does not open a
   gump. That distinction is the whole design — `openSellGump` says `vendor sell` *out loud*, so
   polling by opening the gump would have the character talking to itself every few seconds all
   afternoon.
3. **Sells when `SELL_AT` (30) of the item have piled up**, or when the pack is down to its last
   slots (`SELL_AT_SLOTS`) and there is something of yours to sell — a container holds 125 items,
   and a pack filling with something else still needs the room the watched item is taking.
4. **Backs off when a sale takes nothing.** Out of earshot, out of gold, or refused in silence all
   look the same from here, and none is fixed by asking again straight away. The pause grows each
   time, and after `MAX_QUIET_SALES` in a row the run stops rather than standing there indefinitely.

It counts by **graphic**, not by name — a graphic is on the item already, while a name may have to
be asked for, and `hoist.ts` stops asking after three unanswered tooltips. That latch never resets,
so over a run of hours a name-based count could go blind for the rest of the session. The sale still
matches by name, because a vendor gump has nothing else to match on.

### Before you paste either

- **Stand next to the vendor** you want to sell to. Both scripts say `vendor sell` out loud and take
  whoever answers. `sell-watch` needs you to stay there.
- Have the item somewhere in your pack. Bags are fine.

### How to run them

```bash
npm run build
```

Paste `dist/sell.js`. It will ask you to target the item; click one. The console names what it is
selling, reports each pass, and closes with the total.

`dist/sell-watch.js` is the same first step, and then goes quiet apart from a heartbeat every 30s
until a sale is due. Stop it the way you stop any script in the client.

## What to set

Everything lives in [`config.ts`](config.ts). There is nothing here that has to be calibrated before
the first run.

| Setting | Default | What it is for |
| --- | --- | --- |
| `KEEP` | `0` | Leave this many behind in your pack |
| `HOIST_FROM_BAGS` | `false` | Move matching items out of bags before selling. Off, because this shard's vendors already see into bags — turn it on only where they do not |
| `MAX_PASSES` | 10 | How many times the gump may be reopened |
| `MAX_HOIST_PASSES` | 5 | How many times the pack may be rescanned while items are still shifting out of bags |
| `GUMP_TIMEOUT` | 5s | How long the vendor gump may take to arrive |
| `SELL_DELAY` | 1.5s | The pause before reopening the gump, paid only when a pass is actually due |
| `SALE_TIMEOUT` / `SALE_POLL` | 3s / 200ms | How long the goods are watched for as they leave the pack |
| `OPL_TIMEOUT` | 2s | How long to wait for tooltip data on the targeted item |
| `MOVE_DELAY` / `OPEN_DELAY` | 600ms / 800ms | Hoisting pacing |

`sell-watch` only:

| Setting | Default | What it is for |
| --- | --- | --- |
| `SELL_AT` | 30 | How many of the item have to pile up before a sale is due |
| `SELL_AT_SLOTS` | 110 | Sell early once the pack is this close to the 125-item container cap |
| `WATCH_POLL` | 5s | How often the pack is counted. Silent, so it can be brisk |
| `WATCH_BACKOFF` / `WATCH_BACKOFF_MAX` | 10s / 120s | The growing pause after a sale that took nothing |
| `MAX_QUIET_SALES` | 5 | Fruitless sales in a row before the run gives up |

## When it goes wrong

**`nothing targeted`.** The cursor was cancelled, or the click did not resolve. Run it again.

**`no name for 0x…, the vendor list can only be matched by name`.** The client has no tooltip data
for what you clicked and the gump can only be matched by name, so there is nothing to work with.
Hover the item and try again.

**`no 'X' on offer. Vendor listed: …`.** This vendor does not buy it. The listing tells you what they
do buy. If the item is clearly in your pack and the vendor plainly deals in it, the shard may be one
whose vendors *are* blind to sub-containers after all — turn `HOIST_FROM_BAGS` on and try again.

**`stalled with N left, vendor is not taking them`.** The vendor refused, silently — usually out of
gold. Nothing was lost; the goods are still in your pack.

**`sell-watch: nothing sold (n/5), waiting Ns`.** A sale came back empty. Usually you have wandered
out of earshot, or the vendor is out of gold. It keeps watching, waiting longer each time, and stops
after five. It also covers a subtler case: `sell-watch` counts by art and sells by name, so an item
sharing the graphic but not the name — a magic version of the same weapon — counts toward the
threshold and then will not sell.

**`sell-watch` never fires.** Check the count it printed on the first line. If it says `0x0`, nothing
knew the item's graphic, and a graphic of zero matches nothing on purpose. Hover the item and run it
again.

## Notes on the shard

Written against UOAlive.

- **`target.query()` answers a click with `{serial, graphic, x, y, z, hue}`, and that return is the
  *only* place the clicked serial shows up.** It does not move `target.lastSerial`, which still
  holds whatever was targeted before — so comparing `lastSerial` either side of a `query()` reads a
  second run against the same item as a cancelled cursor. [`pick.ts`](pick.ts) reads the serial off
  the return value for exactly this reason.
- **A vendor's sell gump reaches into your bags.** It lists what is inside a container in your pack
  and sells it from there, which is what stock RunUO does — its `GenericSellInfo` walks the backpack
  recursively. This entry used to claim the opposite, and everything built on it was wrong in two
  ways that only showed once the hoist was turned off. `waitForSale` proved a sale by watching the
  goods leave the *top level*, so an item offered out of a bag was never there to begin with and read
  as gone the instant it was offered — every silent refusal came back as a completed sale. And the
  reopen test counted the top level too, so a run stopped with the bags still full. Both now count
  the whole pack at any depth, which is right whichever way a shard behaves.
  [`hoist.ts`](hoist.ts) still has the hoisting code behind `HOIST_FROM_BAGS`, off, for a shard where
  the old claim is true.
- **`client.sendSellRequest` returns whether the packet went out, not whether the vendor took
  anything,** and a vendor that refuses does so in silence. The goods leaving the pack is the only
  proof a sale landed, so `waitForSale` in [`lib/vendor.ts`](../lib/vendor.ts) polls the pack for the
  offered serials. That is also what stopped this script saying `vendor sell` twice a run: the second
  gump used to exist only to find out whether the first pass had worked, and it costs speech and a 5s
  wait to answer a question the backpack answers for free. The gump is now reopened only when
  matching items are genuinely still loose in the pack, which is the case the multi-pass was written
  for.
- Item names are empty until the client has tooltip data for them, and asking again costs a round
  trip per item — so only the nameless ones are worth an OPL query.
- The gump is matched by name **exactly**, not as a substring, which is the opposite of how
  [`src/boxes`](../boxes/README.md) searches your pack. Deliberately: naming the wrong thing in your
  own pack costs an item that will not move, while naming the wrong thing at the vendor sells
  something you meant to keep.
