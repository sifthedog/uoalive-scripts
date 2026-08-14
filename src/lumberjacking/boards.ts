import { collectIn } from '../lib/containers.js';
import { createConverter } from '../lib/convert.js';
import { isLog } from './chop.js';
import {
  BOARD_GRAPHICS,
  CONVERT_ATTEMPTS,
  CONVERT_DELAY,
  CONVERT_POLL,
  CONVERT_TIMEOUT,
  LOG_GRAPHICS,
  MAX_CONVERT_PASSES,
  TARGET_TIMEOUT,
  UNSKILLED_TEXT,
} from './config.js';
import { isSaving } from './save.js';

export const isBoard = (item: Item): boolean => BOARD_GRAPHICS.has(item.graphic);

const converter = /* @__PURE__ */ createConverter({
  label: 'makeBoards',
  leftAs: 'leaving it as logs',
  attempts: CONVERT_ATTEMPTS,
  timeoutMs: CONVERT_TIMEOUT,
  pollMs: CONVERT_POLL,
  delayMs: CONVERT_DELAY,
  maxPasses: MAX_CONVERT_PASSES,
  unskilledText: UNSKILLED_TEXT,
  isSaving,

  nextStack: (writtenOff) =>
    collectIn(player.backpack?.contents, isLog).find((item) => !writtenOff.has(item.hue ?? 0)),

  // Boards are the tool used and the resource targeted - the inverse of smelting, where the ore is
  // double-clicked and the forge is the target
  perform: (stack) => {
    target.cancel();
    journal.clear();
    player.useItemInHand();

    if (!target.waitTargetEntity(stack.serial, TARGET_TIMEOUT)) {
      target.cancel();
      log('makeBoards: no target cursor, nothing usable in hand?');
      return false;
    }

    return true;
  },

  known: () => [LOG_GRAPHICS, BOARD_GRAPHICS],
  learn: (graphic) => BOARD_GRAPHICS.add(graphic),
  learned: 'board graphic',
});

// Hues this run has given up on. Exported because these are the only logs the haul is allowed to
// put on the animal: everything else is a log that should still become a board.
export const unconvertible = converter.writtenOff;

export const makeBoards = converter.run;

// Not called from the main loop the way mining's is - a wood written off here still gets hauled
// rather than ending the run - but the haul asks before it carries logs across as logs.
export const retryUnconvertible = converter.retry;
