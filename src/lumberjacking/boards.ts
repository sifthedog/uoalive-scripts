import { collectIn, packContents } from '../lib/containers.js';
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
  THROTTLED_TEXT,
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

  // Without it a throttled conversion reads as a verdict on the wood, and three busy moments write
  // hue 0 off - which is every ordinary log. smelt.ts has always passed it; this did not.
  throttledText: THROTTLED_TEXT,
  isSaving,

  nextStack: (writtenOff) =>
    collectIn(packContents(), isLog).find((item) => !writtenOff.has(item.hue ?? 0)),

  // The tool is used and the resource targeted - the inverse of smelting
  perform: (stack) => {
    // Cancelled only when there is one to cancel: an unconditional cancel shortly before the action
    // leaves target.open false for the cursor that follows, the same fix dig.ts and chop.ts carry.
    if (target.open) {
      target.cancel();
    }

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

// The only logs the haul is allowed to put on the animal: everything else should still become a board.
export const unconvertible = converter.writtenOff;

export const makeBoards = converter.run;

// Asked by the haul before it carries logs across as logs, not by the main loop: a wood written off
// here still gets hauled rather than ending the run.
export const retryUnconvertible = converter.retry;
