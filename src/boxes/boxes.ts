import { collectIn, openContainers } from '../lib/containers.js';
import { hex } from '../lib/entity.js';
import {
  BOX_GRAPHICS,
  BOX_NAME,
  CLOSE_BOXES,
  CLOSE_TIMEOUT,
  DROP_KEYS,
  KEY_GRAPHICS,
  MAX_EMPTY_PASSES,
  MOVE_DELAY,
  OPEN_DELAY,
} from './config.js';
import { dropToGround } from './drop.js';

export type EmptyOutcome = 'emptied' | 'stalled' | 'unopened';

let boxGraphic: number | undefined;
let keyGraphic: number | undefined;

export { hex };

// Finding a box by name is a substring test, which is the opposite of how the *sell gump* is
// matched. Deliberately: naming the wrong thing here costs a box that will not open and gets
// skipped, while naming the wrong thing at the vendor sells something you meant to keep.
export const isBox = (item: Item): boolean =>
  (boxGraphic !== undefined && item.graphic === boxGraphic) ||
  BOX_GRAPHICS.has(item.graphic) ||
  (item.name ?? '').toLowerCase().includes(BOX_NAME);

// A whole word, not a substring: 'key' inside 'monkey' or 'turkey' would put something on the
// floor that was never meant to go there, and what a key is decides that now
const KEY_WORD = /\bkey\b/i;

export const isKey = (item: Item): boolean =>
  (keyGraphic !== undefined && item.graphic === keyGraphic) ||
  KEY_GRAPHICS.has(item.graphic) ||
  KEY_WORD.test(item.name ?? '');

// The same trick as rememberBox: names arrive only with tooltip data, so the first key the client
// can describe teaches the run the art and the nameless ones behind it are recognised on sight
const rememberKey = (item: Item): void => {
  if (keyGraphic === undefined && !KEY_GRAPHICS.has(item.graphic)) {
    keyGraphic = item.graphic;
    log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to KEY_GRAPHICS`);
  }
};

// A box found by name teaches the run its graphic. Returns whether it learned something, because
// the scan that found it has to be redone once it has: only the boxes the client had tooltip data
// for matched by name, and the rest of the pile is sitting there nameless with the same graphic.
export const rememberBox = (item: Item | undefined): boolean => {
  if (!item || boxGraphic !== undefined || BOX_GRAPHICS.has(item.graphic)) {
    return false;
  }

  boxGraphic = item.graphic;
  log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to BOX_GRAPHICS`);
  return true;
};

// collectIn recurses, so a box sitting inside another bag is found too - but a container's contents
// stay undefined until it has been opened, so an unopened bag hides everything in it. That is the
// second reason a full pack can report nothing, and it costs one pass of double-clicks to rule out.
export const findBoxes = (): Item[] => {
  let boxes = collectIn(player.backpack?.contents, isBox);

  if (boxes.length === 0 && openContainers()) {
    boxes = collectIn(player.backpack?.contents, isBox);
  }

  if (rememberBox(boxes[0])) {
    boxes = collectIn(player.backpack?.contents, isBox);
  }

  return boxes;
};

// A container's window is looked up under the container's own serial, the way tinkering/gump.ts
// looks up the craft gump. If container windows are not gumps in that sense the lookup simply
// answers nothing - better than closing the character window along with everything else.
export const closeBox = (serial: number): void => {
  if (CLOSE_BOXES !== 'perBox') {
    return;
  }

  if (Gump.exists(serial)) {
    Gump.findOrWait(serial, CLOSE_TIMEOUT)?.close();
  }
};

// The blunt one, kept behind a config value: it shuts every gump on screen, character sheet and
// paperdoll included, because the client has no per-container close
export const closeEverything = (): void => {
  if (CLOSE_BOXES === 'allGumps') {
    client.closeAllGumps();
  }
};

// What to look at when nothing matched: the graphic that repeats as often as you have boxes is the
// one to put in BOX_GRAPHICS
export const dumpPack = (): void => {
  log('boxes: pack contents (graphic / hue / amount / name)');

  for (const item of player.backpack?.contents ?? []) {
    log(
      `boxes:   ${hex(item.graphic)} hue ${item.hue ?? 0} x${item.amount ?? 1} "${item.name ?? ''}"`,
    );
  }
};

// findObject answers with an Item or a Mobile, and only an Item has contents. Asked as "not a
// Mobile" rather than "is an Item", the way haul.ts does it: _tag is a discriminant in the client's
// typings and only the Mobile side is ever observed carrying it at runtime.
const resolveItem = (serial: number): Item | undefined => {
  const found = client.findObject(serial);
  return found && found._tag !== 'Mobile' ? found : undefined;
};

export interface Emptied {
  outcome: EmptyOutcome;
  moved: Item[];
  // Recognised as keys, and of those, the ones that made it to the floor. Kept apart so the run
  // can say which of the two failures happened: nothing recognised, or nothing landing.
  keys: Item[];
  dropped: Item[];
}

// A container's contents stay undefined until it has been opened, so the double-click comes first.
// Contents that are still undefined afterwards mean the box never opened - locked, most likely -
// and that is reported rather than guessed at, because only a box watched going empty is ever sold.
//
// Moves are asynchronous, so the box is re-resolved and rescanned between passes rather than
// trusting moveItem's return value. A pass that shifts nothing is a stall, not an empty box.
export const emptyBox = (boxSerial: number, packSerial: number): Emptied => {
  player.use(boxSerial);
  sleep(OPEN_DELAY);

  // Keyed by serial, so an item that a failed move left behind is not counted twice
  const moved = new Map<number, Item>();
  const keys = new Map<number, Item>();
  const dropped = new Map<number, Item>();

  const result = (outcome: EmptyOutcome): Emptied => ({
    outcome,
    moved: [...moved.values()],
    keys: [...keys.values()],
    dropped: [...dropped.values()],
  });

  let previous = Infinity;

  for (let pass = 0; pass < MAX_EMPTY_PASSES; pass++) {
    const contents = resolveItem(boxSerial)?.contents;

    if (contents === undefined) {
      return result('unopened');
    }

    if (contents.length === 0) {
      return result('emptied');
    }

    if (contents.length >= previous) {
      return result('stalled');
    }
    previous = contents.length;

    // Keys go on the floor, everything else into the pack. That way round on purpose: an art this
    // does not recognise as a key ends up somewhere safe rather than on the ground. A drop that
    // will not land is recoverable the same way - the key goes in the pack and the run carries on.
    for (const item of contents) {
      const looksLikeKey = isKey(item);

      if (looksLikeKey) {
        rememberKey(item);
        keys.set(item.serial, item);
      }

      if (looksLikeKey && DROP_KEYS && dropToGround(item, boxSerial)) {
        dropped.set(item.serial, item);
      } else {
        player.moveItem(item.serial, packSerial);
      }

      moved.set(item.serial, item);
      sleep(MOVE_DELAY);
    }
  }

  return result('stalled');
};
