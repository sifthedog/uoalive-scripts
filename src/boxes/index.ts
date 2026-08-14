import { die } from '../lib/die.js';
import { closeBox, closeEverything, dumpPack, emptyBox, findBoxes, hex } from './boxes.js';
import { DROP_KEYS, LOG_EVERY_BOX, MAX_ROUNDS, SELL } from './config.js';
import { stopReason } from './guards.js';
import { peekContents } from './peek.js';
import { sellBoxes } from './sale.js';

const backpack = player.backpack ?? die('boxes: no backpack');

// Boxes proved empty, and boxes that would not empty. Both carry across rounds: a box emptied in
// one round is still in the pack until it sells, and a box that would not open must not be tried
// again every round.
const emptied = new Set<number>();
const refused = new Set<number>();

let stop: string | undefined;
let keysSeen = 0;
let keysDropped = 0;
let keptBack = 0;
let soldTotal = 0;
const graphicsSeen = new Set<number>();

const initial = findBoxes();
log(`boxes: ${initial.length} wooden boxes in the pack`);

// A pack that plainly has boxes in it and reports none means the graphic is wrong for this shard,
// so say what is actually in there rather than stopping with nothing to go on
if (initial.length === 0) {
  dumpPack();
  die('boxes: nothing matched - pick your box out of the dump above and put its graphic in BOX_GRAPHICS');
}

for (let round = 0; round < MAX_ROUNDS && !stop; round++) {
  const todo = findBoxes().filter((box) => !emptied.has(box.serial) && !refused.has(box.serial));

  let guard: string | undefined;
  let openedThisRound = 0;
  let skippedEmpty = 0;

  for (const box of todo) {
    guard = stopReason();
    if (guard) {
      break;
    }

    // The shard's own tooltip says how much is in a box, which costs a query rather than a
    // double-click and an 800ms wait. "Contents: 0" is the server stating the box is empty, which
    // is a better answer than the client-side contents array the opening path has to rely on, so
    // it counts as confirmed and the box is safe to sell. Anything else, or no tooltip at all,
    // falls through to opening it.
    const inside = peekContents(box.serial);

    if (inside === 0) {
      emptied.add(box.serial);
      skippedEmpty++;

      if (LOG_EVERY_BOX) {
        log(`boxes: ${hex(box.serial)} already empty, not opening it`);
      }

      continue;
    }

    const { outcome, moved, keys, dropped } = emptyBox(box.serial, backpack.serial);

    keysSeen += keys.length;
    keysDropped += dropped.length;
    keptBack += moved.length - dropped.length;

    for (const item of moved) {
      graphicsSeen.add(item.graphic);
    }

    if (outcome === 'emptied') {
      emptied.add(box.serial);
      openedThisRound++;
    } else {
      refused.add(box.serial);
    }

    closeBox(box.serial);

    if (LOG_EVERY_BOX) {
      const describe = (item: Item) =>
        `${hex(item.graphic)}${dropped.includes(item) ? ' -> floor' : ' -> pack'}`;
      const contents = moved.map(describe).join(', ') || 'nothing';
      log(`boxes: ${hex(box.serial)} ${outcome}, took out ${contents}`);
    }
  }

  const skippedNote = skippedEmpty ? `, ${skippedEmpty} already empty` : '';
  const refusedNote = refused.size ? `, ${refused.size} would not open` : '';
  log(`boxes: round ${round + 1}, emptied ${openedThisRound}${skippedNote}${refusedNote}`);

  // Said out loud rather than kept for the stop message. A guard that fires before the first box
  // leaves a round that did nothing and explained nothing, which is how "emptied 0" arrived with
  // no reason attached.
  if (guard) {
    log(`boxes: stopped going through the boxes - ${guard}`);
  }

  if (!SELL) {
    stop = guard ?? `SELL is off, ${emptied.size} boxes emptied and left in the pack`;
    break;
  }

  // Asked of the pack rather than counted from this round, so a guard that cut the emptying short
  // still leaves the sale knowing there are boxes in there nobody has looked inside
  const unconfirmed = findBoxes().filter((box) => !emptied.has(box.serial)).length;
  const sold = sellBoxes(emptied, unconfirmed);
  soldTotal += sold;

  // A round that only skipped already-empty boxes still made progress, so it is not a stall
  if (sold === 0) {
    stop =
      openedThisRound + skippedEmpty
        ? 'the vendor took nothing'
        : (guard ?? 'nothing left to empty and nothing sold');
    break;
  }

  if (todo.length === 0) {
    stop = refused.size
      ? `${refused.size} boxes would not open, everything else is dealt with`
      : 'every box is dealt with';
  }
}

closeEverything();

const keptNote = keptBack ? `, ${keptBack} other items into the pack` : '';

log(
  `boxes: ${soldTotal} sold, ${keysDropped} of ${keysSeen} keys on the floor${keptNote}, ` +
    `${refused.size} boxes left unopened. ` +
    `Graphics taken out of boxes: ${[...graphicsSeen].map(hex).join(', ') || 'none'}`,
);

// The two ways this goes wrong look identical from the outside, so name which one it was
if (keysSeen === 0 && keptBack > 0) {
  log(
    'boxes: nothing came out of a box looked like a key, so it all went into the pack. Put the ' +
      'graphic listed above into KEY_GRAPHICS in config.ts.',
  );
} else if (DROP_KEYS && keysDropped < keysSeen) {
  log(`boxes: ${keysSeen - keysDropped} keys were recognised but would not leave the box.`);
}

exit(`boxes: ${stop ?? `hit the ${MAX_ROUNDS} round backstop`}`);
