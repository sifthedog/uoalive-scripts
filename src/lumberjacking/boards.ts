import { collectIn } from '../lib/containers.js';
import { countsByGraphic, diffCounts, type Change, type Counts } from '../lib/pack.js';
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

// Hues this run has given up on. Exported because these are the only logs the haul is allowed to
// put on the animal: everything else is a log that should still become a board.
export const unconvertible = new Set<number>();

export const isBoard = (item: Item): boolean => BOARD_GRAPHICS.has(item.graphic);

// The conversion sends no message on stock RunUO, only a sound, so the pack diff is the only
// evidence of it. That diff also names the board graphic, whatever this shard's art id is.
const learnBoards = (changes: Change[]): void => {
  for (const { key, delta } of changes) {
    if (delta <= 0) {
      continue;
    }

    const graphic = Number(key.split('/')[0]);
    if (LOG_GRAPHICS.has(graphic) || BOARD_GRAPHICS.has(graphic)) {
      continue;
    }

    BOARD_GRAPHICS.add(graphic);
    log(`makeBoards: board graphic is 0x${graphic.toString(16)}`);
  }
};

// Watch the pack rather than sleeping a fixed amount and reading once. The action throttle can
// hold a conversion well past any pause worth taking, and reading too early is indistinguishable
// from a wood that cannot be worked - which is how ordinary logs ended up on the animal.
const waitForChange = (before: Counts): Change[] => {
  for (let waited = 0; waited < CONVERT_TIMEOUT; waited += CONVERT_POLL) {
    sleep(CONVERT_POLL);

    const changes = diffCounts(before, countsByGraphic());
    if (changes.length > 0) {
      return changes;
    }
  }

  return [];
};

// Silent misses per hue, cleared by a success, so only a hue that fails repeatedly is given up on
const misses = new Map<number, number>();

// Counts one failure against a hue and gives up on it once they add up. Every failing path has to
// come through here: one that returned without counting left the candidate set unchanged, so the
// next pass picked the same stack and the loop ran to its backstop instead of shrinking.
const missed = (stackHue: number): void => {
  const count = (misses.get(stackHue) ?? 0) + 1;
  misses.set(stackHue, count);

  if (count >= CONVERT_ATTEMPTS) {
    unconvertible.add(stackHue);
    log(`makeBoards: hue ${stackHue} failed ${count} times, leaving it as logs`);
  }
};

const convert = (stack: Item): boolean => {
  const stackHue = stack.hue ?? 0;
  const before = countsByGraphic();

  // A cursor left open by the last chop would swallow this one
  target.cancel();
  journal.clear();
  player.useItemInHand();

  if (!target.waitTargetEntity(stack.serial, TARGET_TIMEOUT)) {
    target.cancel();
    log('makeBoards: no target cursor, nothing usable in hand?');
    // Counted like any other failure. Without this a hand with no axe in it - dead, just broken,
    // mid-swap - spent every pass of the loop waiting on a cursor that was never going to come.
    missed(stackHue);
    return false;
  }

  const changes = waitForChange(before);
  if (changes.length > 0) {
    misses.delete(stackHue);
    learnBoards(changes);
    return true;
  }

  // The shard saying it outright is worth acting on immediately; a special wood needs the
  // Lumberjacking to work it, and no amount of retrying supplies that.
  if (UNSKILLED_TEXT.some((text) => journal.containsText(text))) {
    unconvertible.add(stackHue);
    log(`makeBoards: not skilled enough for hue ${stackHue}, leaving it as logs`);
    return false;
  }

  // Otherwise it was silent, which is also what a throttled or stale attempt looks like
  missed(stackHue);

  return false;
};

export const makeBoards = (): boolean => {
  // One stack per pass, then rescan: a conversion consumes the stack and creates a new item, so
  // every other serial in a snapshot goes stale the moment the first one converts.
  for (let pass = 0; pass < MAX_CONVERT_PASSES; pass++) {
    // A frozen shard answers a conversion the same way an unworkable wood does - with nothing at
    // all - so without this a world save costs CONVERT_ATTEMPTS and the hue is written off for the
    // rest of the run. Left for the caller: the pack is still heavy, so the next haul comes back.
    if (isSaving()) {
      log('makeBoards: the world is saving, leaving the logs for now');
      return false;
    }

    const stack = collectIn(player.backpack?.contents, isLog).find(
      (item) => !unconvertible.has(item.hue ?? 0),
    );

    if (!stack) {
      return true;
    }

    convert(stack);
    sleep(CONVERT_DELAY);
  }

  // Termination does not rest on this: a hue either converts or is given up on after
  // CONVERT_ATTEMPTS, so the candidate set always shrinks. This is the backstop.
  log(`makeBoards: hit the ${MAX_CONVERT_PASSES} pass backstop`);
  return false;
};
