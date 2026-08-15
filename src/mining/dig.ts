import { describeItem } from '../lib/entity.js';
import { outcomeVocabulary } from '../lib/outcomes.js';
import { DIG_TIMEOUT, NO_CURSOR_READ, OUTCOME_TEXT, TARGET_TIMEOUT } from './config.js';
import { oreTotal } from './ore.js';

// The outcomes the shard words itself, plus the two the world is read for when it stays silent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type DigOutcome = Outcome | 'noCursor' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// A shard that words its harvest messages differently leaves the journal silent, so read the world
// instead. Ore landing in the pack is the only proof of a swing that does not depend on wording.
const silentOutcome = (serial: number | undefined, oreBefore: number): DigOutcome => {
  if (serial !== undefined && !client.findObject(serial)) {
    return 'wornOut';
  }

  if (oreTotal() > oreBefore) {
    return 'dug';
  }

  return 'unknown';
};

// No cursor is not the same as nothing having happened: the commonest reason a shard declines a
// swing is that it refused the action outright and said so, and the journal has been clear since
// immediately before this swing. Reaching noCursor instead of the throttled or saving branch is what
// ended a live run in fifteen seconds with a pickaxe plainly in hand.
const refusedOutcome = (
  serial: number | undefined,
  oreBefore: number,
  cursorCameLate: boolean,
): DigOutcome | undefined => {
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, NO_CURSOR_READ);
  if (matched) {
    return outcomeFor(matched);
  }

  const silent = silentOutcome(serial, oreBefore);
  if (silent !== 'unknown') {
    return silent;
  }

  // A cursor that turned up just too late is a different fault from one that never came -
  // TARGET_TIMEOUT rather than the shard - and they look alike without saying which.
  log(
    `digOnce: no target cursor - hand ${describeItem(player.equippedItems.oneHanded)}, ` +
      `cursor ${cursorCameLate ? 'came late' : 'never opened'}`,
  );

  return 'noCursor';
};

// Takes no vein, unlike lumberjacking's chopOnce, because the swing is aimed by where you stand.
//
// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has a default for it, so the maybe is kept rather than asserted away.
export const digOnce = (serial: number | undefined): DigOutcome | undefined => {
  // A cursor left open by the previous swing would swallow this one
  target.cancel();

  const oreBefore = oreTotal();
  journal.clear();

  player.useItemInHand();

  // Answered with yourself rather than with the vein's coordinates: the shard takes that as "mine
  // where I am" and picks the ore itself, where an explicit target.terrain has to guess right about
  // land versus static and about which art on the tile carries the ore.
  if (!target.waitTargetSelf(TARGET_TIMEOUT)) {
    // Read before the cancel closes it, or the answer is always 'no cursor' and says nothing
    const cursorCameLate = target.open;

    target.cancel();

    return refusedOutcome(serial, oreBefore, cursorCameLate);
  }

  // author is left undefined on purpose: a shard may route harvest text through the pickaxe as
  // object text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, DIG_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(serial, oreBefore);
};
