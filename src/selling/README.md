# selling — sell every stack of the items you point at

Builds two scripts:

| Script | What it does |
| --- | --- |
| `dist/sell.js` | Target items until you press ESC, sell every stack of them, stop |
| `dist/sell-watch.js` | Target items until you press ESC, then keep selling them in batches as the pack fills |

## Why it exists

Clearing forty stacks out of a sell gump by hand is forty clicks — repeated, because the gump only
lists so many entries at a time. Point at the items and the script sells every stack of them.

`sell-watch` is the same sale on a timer, for when you are producing the items rather than clearing
them out.

## What `sell` does

1. **Asks you to target items, one click each, until you press ESC.** The serial comes off
   `target.query()`'s return value, and the name off the tooltip — an item you have never hovered
   has no name until the client has OPL data for it. A click on something nothing can name is
   skipped and the selection carries on; the same name twice is taken once. `MAX_PICKS` (20) is a
   backstop, not the way the selection is meant to end.
2. **Says `vendor sell` once** and matches the gump's entries against every name you picked —
   exactly and case-insensitively, never as a substring, so targeting a `wooden box` does not sweep
   up `small wooden box`. All of them go through the one gump: reopening it costs another
   `vendor sell`, and the gump the vendor already has open lists them all anyway.
3. **Sends one sell request** and then watches the goods leave the pack, which is the only proof the
   vendor took anything. Attributed per stack, so the report says which of your items sold.
4. **Reopens the gump** only if matching items are genuinely still in the pack — a sell gump lists a
   limited number of entries, so a pile too big to list at once needs another pass.

`KEEP` is per item: 10 leaves 10 of *each* name behind, not 10 between them.

There is a hoisting step (`HOIST_FROM_BAGS`) that moves matching items out of bags before the sale.
It is **off**, because this shard's vendors read a bag as readily as the top of the pack — see
*Notes on the shard*. Turn it on only if yours does not.

## What `sell-watch` adds

1. **Targets once** — the same click-until-ESC selection — then loops.
2. **Counts the pack every `WATCH_POLL`, silently.** Counting reads the pack; it does not open a
   gump. That distinction is the whole design — `openSellGump` says `vendor sell` *out loud*, so
   polling by opening the gump would have the character talking to itself every few seconds all
   afternoon.
3. **Sells when `SELL_AT` (100) of the watched items have piled up between them**, or when the pack
   is down to its last slots (`SELL_AT_SLOTS`) — a pack filling with something else still needs the
   room the watched items are taking. The threshold is the combined count, because a pack filling
   with three things fills exactly as fast as one.
4. **Backs off when a sale takes nothing.** Out of earshot, out of gold, or refused in silence all
   look the same from here, and none is fixed by asking again straight away. The pause grows each
   time, and after `MAX_QUIET_SALES` in a row the run stops rather than standing there indefinitely.

It counts by **graphic**, not by name — a graphic is on the item already, while a name may have to
be asked for, and `hoist.ts` stops asking after three unanswered tooltips, a latch that never resets.
The sale still matches by name, because a vendor gump has nothing else to match on. A pick nothing
knows the art for is named out loud at the start: it cannot be counted, so it would sit unsold behind
a threshold it can never reach.

### Before you paste either

- **Stand next to the vendor** you want to sell to. Both scripts say `vendor sell` out loud and take
  whoever answers. `sell-watch` needs you to stay there.
- Have the items somewhere in your pack. Bags are fine.
- **Hover anything you have not looked at before.** The name comes from tooltip data, and a click on
  an item the client has none for is skipped.

### How to run them

```bash
npm run build
```

Paste `dist/sell.js`. It will ask you to target items: click each one, then press **ESC** to finish.
The console numbers them as you go, reports each pass, and closes with a total per item.

```
sell: target the items you want to sell, ESC when done
sell:   1. iron ingot
sell:   2. scimitar
sell: selling 'iron ingot', 'scimitar'
sell: pass 1, offered 240 x 'iron ingot', 2 x 'scimitar', vendor took 240 x 'iron ingot', 2 x 'scimitar'
sell: 240 x 'iron ingot', 2 x 'scimitar' sold, 242 in all
```

`dist/sell-watch.js` is the same first step, and then goes quiet apart from a heartbeat every 30s
until a sale is due. Stop it the way you stop any script in the client.

## What to set

Everything lives in [`config.ts`](config.ts). There is nothing here that has to be calibrated before
the first run.

| Setting | Default | What it is for |
| --- | --- | --- |
| `KEEP` | `0` | Leave this many of each item behind in your pack |
| `MAX_PICKS` | 20 | How many clicks one selection takes before it stops asking. A backstop; ESC is how you end it |
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
| `SELL_AT` | 100 | How many of the watched items have to pile up between them before a sale is due. Counted by stack amount, so a single stack of 100 ingots trips it and 100 rings fill 100 slots |
| `SELL_AT_SLOTS` | 110 | Sell early once the pack is this close to the 125-item container cap |
| `WATCH_POLL` | 5s | How often the pack is counted. Silent, so it can be brisk |
| `WATCH_BACKOFF` / `WATCH_BACKOFF_MAX` | 10s / 120s | The growing pause after a sale that took nothing |
| `MAX_QUIET_SALES` | 5 | Fruitless sales in a row before the run gives up |

## When it goes wrong

**`nothing targeted`.** This is what ESC looks like, and it is how the selection is meant to end. It
is also what a click that did not resolve looks like — the two are indistinguishable, so if the list
came out shorter than you clicked, run it again.

**`no name for 0x…, the vendor list can only be matched by name`.** The client has no tooltip data
for what you clicked and the gump can only be matched by name, so there is nothing to work with.
That click is skipped and the selection carries on; hover the item and click it again.

**`the tooltip lookup would not answer`.** The client threw out of `queryItemOPL` instead of
answering — usually `Waiting for script RequestMegaCliloc timed out`. Said once. That item goes
unnamed, and three unanswered in a row latch the lookup off for the rest of the run, exactly as a
tooltip that comes back empty does. Harmless in itself — before it was caught it ended the run, and
it did so *after* the vendor had paid. If the item is plainly named on screen and this still fires,
the tooltip is arriving slower than `OPL_TIMEOUT`.

**`nothing of X, Y on offer. Vendor listed: …`.** This vendor buys none of them. The listing tells
you what they do buy. If an item is clearly in your pack and the vendor plainly deals in it, the
shard may be one whose vendors *are* blind to sub-containers after all — turn `HOIST_FROM_BAGS` on
and try again.

**`stalled with N left, vendor is not taking them`.** The vendor refused, silently — usually out of
gold. Nothing was lost; the goods are still in your pack.

**`sell-watch: nothing sold (n/5), waiting Ns`.** A sale came back empty. Usually you have wandered
out of earshot, or the vendor is out of gold. It keeps watching, waiting longer each time, and stops
after five. It also covers a subtler case: `sell-watch` counts by art and sells by name, so an item
sharing the graphic but not the name — a magic version of the same weapon — counts toward the
threshold and then will not sell.

**`sell-watch` never fires.** Check the arts it printed on the first line. Anything showing `0x0` is
an item nothing knew the graphic for, and a graphic of zero matches nothing on purpose — the run
says so at the start. Hover it and run again. Remember the threshold is the combined count: three
items reach 30 between them, so a sale can fire with ten of each.

## Notes on the shard

Written against UOAlive.

- **`target.query()` answers a click with `{serial, graphic, x, y, z, hue}`, and that return is the
  *only* place the clicked serial shows up.** It does not move `target.lastSerial`, which still
  holds whatever was targeted before — so comparing `lastSerial` either side of a `query()` reads a
  second run against the same item as a cancelled cursor. [`lib/pick.ts`](../lib/pick.ts) reads the serial
  off the return value for exactly this reason.
- **There is no ESC event.** Nothing in `types/classicuo.d.ts` reports a key, and the only `cancel`
  in the API is `target.cancel()`, which *closes* a cursor rather than telling you about one. What
  ESC produces is a `query()` that comes back without a serial — the same answer a click that
  resolved to nothing gives — and that is the entire basis of the loop in [`lib/pick.ts`](../lib/pick.ts). It
  also means `query()` has no timeout: a run where you neither click nor press ESC waits for you
  indefinitely.
- **A vendor's sell gump reaches into your bags**, which is what stock RunUO's `GenericSellInfo`
  does. This entry used to claim the opposite, and two things built on it were wrong: `waitForSale`
  proved a sale by watching the goods leave the *top level*, so an item offered out of a bag read as
  gone the instant it was offered and every silent refusal came back as a completed sale; and the
  reopen test counted the top level too, so a run stopped with the bags still full. Both now count
  the whole pack at any depth. The hoisting code stays behind `HOIST_FROM_BAGS`, off, for a shard
  where the old claim is true.
- **`client.sendSellRequest` returns whether the packet went out, not whether the vendor took
  anything,** and a vendor that refuses does so in silence. The goods leaving the pack is the only
  proof, so `waitForSale` in [`lib/vendor.ts`](../lib/vendor.ts) polls the pack for the offered
  serials. That is also what stopped this script saying `vendor sell` twice a run: the second gump
  existed only to find out whether the first pass had worked, which the backpack answers for free.
- Item names are empty until the client has tooltip data for them, and asking again costs a round
  trip per item — so only the nameless ones are worth an OPL query.
- The gump is matched by name **exactly**, not as a substring, which is the opposite of how
  [`src/boxes`](../boxes/README.md) searches your pack. Deliberately: naming the wrong thing in your
  own pack costs an item that will not move, while naming the wrong thing at the vendor sells
  something you meant to keep.
