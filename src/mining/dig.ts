import { DIG_TIMEOUT, OUTCOME_TEXT, TARGET_TIMEOUT } from './config.js';
import { oreTotal } from './ore.js';

// The outcomes the shard words itself, plus the two the world is read for when it stays silent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type DigOutcome = Outcome | 'noCursor' | 'unknown';

export const ALL_OUTCOME_TEXT = Object.values(OUTCOME_TEXT).flat();

export const outcomeFor = (matched: string): Outcome | undefined =>
  (Object.keys(OUTCOME_TEXT) as Outcome[]).find((name) => OUTCOME_TEXT[name].includes(matched));

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
    target.cancel();
    log('digOnce: no target cursor, nothing usable in hand?');
    return 'noCursor';
  }

  // author is left undefined on purpose: a shard may route harvest text through the pickaxe as
  // object text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, DIG_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(serial, oreBefore);
};
