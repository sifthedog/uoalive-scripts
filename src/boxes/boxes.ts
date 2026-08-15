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

// A substring test, which is the opposite of how the *sell gump* is matched. Deliberately: naming
// the wrong thing here costs a box that will not open, while naming the wrong thing at the vendor
// sells something you meant to keep.
export const isBox = (item: Item): boolean =>
  (boxGraphic !== undefined && item.graphic === boxGraphic) ||
  BOX_GRAPHICS.has(item.graphic) ||
  (item.name ?? '').toLowerCase().includes(BOX_NAME);

// A whole word, not a substring: 'key' inside 'monkey' would put something on the floor that was
// never meant to go there
const KEY_WORD = /\bkey\b/i;

export const isKey = (item: Item): boolean =>
  (keyGraphic !== undefined && item.graphic === keyGraphic) ||
  KEY_GRAPHICS.has(item.graphic) ||
  KEY_WORD.test(item.name ?? '');

// Names arrive only with tooltip data, so the first key the client can describe teaches the run the
// art and the nameless ones behind it are recognised on sight
const rememberKey = (item: Item): void => {
  if (keyGraphic === undefined && !KEY_GRAPHICS.has(item.graphic)) {
    keyGraphic = item.graphic;
    log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to KEY_GRAPHICS`);
  }
};

// Returns whether it learned something, because the scan then has to be redone: only the boxes the
// client had tooltip data for matched by name, and the rest of the pile is nameless.
export const rememberBox = (item: Item | undefined): boolean => {
  if (!item || boxGraphic !== undefined || BOX_GRAPHICS.has(item.graphic)) {
    return false;
  }

  boxGraphic = item.graphic;
  log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to BOX_GRAPHICS`);
  return true;
};

// collectIn recurses, but a container's contents stay undefined until it has been opened - so an
// unopened bag hides everything in it, which one pass of double-clicks rules out.
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

// Looked up under the container's own serial, the way a craft gump is looked up under its type id.
// If container windows are not gumps in that sense the lookup simply answers nothing.
export const closeBox = (serial: number): void => {
  if (CLOSE_BOXES !== 'perBox') {
    return;
  }

  if (Gump.exists(serial)) {
    Gump.findOrWait(serial, CLOSE_TIMEOUT)?.close();
  }
};

// Shuts every gump on screen, paperdoll included, because the client has no per-container close
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
// Mobile" because only that side of the _tag discriminant is ever observed at runtime.
const resolveItem = (serial: number): Item | undefined => {
  const found = client.findObject(serial);
  return found && found._tag !== 'Mobile' ? found : undefined;
};

export interface Emptied {
  outcome: EmptyOutcome;
  moved: Item[];
  // Kept apart from `dropped` so the run can say which failure happened: nothing recognised, or
  // nothing landing.
  keys: Item[];
  dropped: Item[];
}

// Contents stay undefined until a container has been opened, so the double-click comes first, and
// contents still undefined afterwards mean the box never opened - reported rather than guessed at,
// because only a box watched going empty is ever sold.
//
// Moves are asynchronous, so the box is rescanned between passes rather than moveItem's return
// value trusted. A pass that shifts nothing is a stall, not an empty box.
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

    // That way round on purpose: an art this does not recognise as a key ends up somewhere safe
    // rather than on the ground, and a drop that will not land falls back to the pack.
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
