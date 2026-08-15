import { describeItem } from '../lib/entity.js';
import { outcomeVocabulary } from '../lib/outcomes.js';
import { totalMatching } from '../lib/pack.js';
import {
  CHOP_TIMEOUT,
  LOG_GRAPHICS,
  NO_CURSOR_READ,
  OUTCOME_TEXT,
  TARGET_TIMEOUT,
} from './config.js';
import type { Tree } from './tree.js';

// The outcomes the shard words itself, plus the two the world is read for when it stays silent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type ChopOutcome = Outcome | 'noCursor' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// Hue-blind on purpose: special woods are hued, and they count toward the pack all the same
export const isLog = (item: Item): boolean => LOG_GRAPHICS.has(item.graphic);

export const logTotal = (contents?: Item[]): number => totalMatching(isLog, contents);

// A shard that words its harvest messages differently leaves the journal silent, so read the world
// instead. Logs landing in the pack is the only proof of a chop that does not depend on wording.
const silentOutcome = (serial: number | undefined, logsBefore: number): ChopOutcome => {
  if (serial !== undefined && !client.findObject(serial)) {
    return 'wornOut';
  }

  if (logTotal() > logsBefore) {
    return 'chopped';
  }

  return 'unknown';
};

// No cursor is not the same as nothing having happened: the commonest reason a shard declines a
// swing is that it refused the action outright and said so, and the journal has been clear since
// immediately before this swing. Reaching noCursor instead of the throttled or saving branch is what
// ended a live mining run in fifteen seconds with a pickaxe plainly in hand.
const refusedOutcome = (
  serial: number | undefined,
  logsBefore: number,
  cursorCameLate: boolean,
): ChopOutcome | undefined => {
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, NO_CURSOR_READ);
  if (matched) {
    return outcomeFor(matched);
  }

  const silent = silentOutcome(serial, logsBefore);
  if (silent !== 'unknown') {
    return silent;
  }

  // A cursor that turned up just too late is a different fault from one that never came -
  // TARGET_TIMEOUT rather than the shard. Two-handed first, the way rememberAxe reads the layers.
  log(
    `chopOnce: no target cursor - hand ` +
      `${describeItem(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded)}, ` +
      `cursor ${cursorCameLate ? 'came late' : 'never opened'}`,
  );

  return 'noCursor';
};

// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has always had a default for it, so the maybe is kept rather than asserted away
export const chopOnce = (tree: Tree, serial: number | undefined): ChopOutcome | undefined => {
  // A cursor left open by the previous swing would swallow this one
  target.cancel();

  const logsBefore = logTotal();
  journal.clear();

  player.useItemInHand();

  if (!target.wait(TARGET_TIMEOUT)) {
    // Read before the cancel closes it, or the answer is always 'no cursor' and says nothing
    const cursorCameLate = target.open;

    target.cancel();

    return refusedOutcome(serial, logsBefore, cursorCameLate);
  }

  // The graphic is not optional here: target.terrain without one targets the land tile under the
  // tree, which the shard answers with a mining message rather than a chop.
  target.terrain(tree.x, tree.y, tree.z, tree.graphic);

  // author is left undefined on purpose: a shard may route harvest text through the axe as object
  // text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CHOP_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(serial, logsBefore);
};
