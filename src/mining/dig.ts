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

// No cursor opened, which is not the same as nothing having happened. The commonest reason a shard
// declines to start a swing is that it refused the action outright and said so - "you must wait",
// "the world is saving", "you have worn out your tool" - and the journal has been clear since
// immediately before this swing, so whatever is in it now arrived because of it. Read that before
// falling back on noCursor: throttled and saving both have branches that back off and cost the run
// nothing, and reaching noCursor instead of them is what ended a live run in fifteen seconds with a
// pickaxe plainly in hand.
//
// silentOutcome after it for the same reason the ordinary path ends there - a tool that broke as it
// swung, or a swing that landed without a word said about it, are both still true here.
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

  // The old wording guessed at an empty hand and was wrong about it. What is actually in the hand is
  // one layer read away, and a cursor that turned up just too late is a different fault from one
  // that never came - TARGET_TIMEOUT rather than the shard - which they look alike without.
  log(
    `digOnce: no target cursor - hand ${describeItem(player.equippedItems.oneHanded)}, ` +
      `cursor ${cursorCameLate ? 'came late' : 'never opened'}`,
  );

  return 'noCursor';
};

// Takes no vein, unlike lumberjacking's chopOnce, because the swing is aimed by where you stand
// rather than by naming a tile - see the target below. The loop still books the answer against the
// vein it walked to; that bookkeeping is its business, not this one's.
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
  // where I am" and picks the ore itself, which works by hand here where an explicit target.terrain
  // has to guess right about land versus static and about which of the arts on a tile is the one
  // carrying ore. The vein is still what the loop walks to and what it books the outcome against -
  // it just aims the swing by standing in the right place rather than by naming a tile.
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
