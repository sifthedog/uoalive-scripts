import { CHOP_TIMEOUT, LOG_GRAPHICS, OUTCOME_TEXT, TARGET_TIMEOUT } from './config.js';
import type { Tree } from './tree.js';

// The outcomes the shard words itself, plus the two the world is read for when it stays silent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type ChopOutcome = Outcome | 'noCursor' | 'unknown';

export const ALL_OUTCOME_TEXT = Object.values(OUTCOME_TEXT).flat();

export const outcomeFor = (matched: string): Outcome | undefined =>
  (Object.keys(OUTCOME_TEXT) as Outcome[]).find((name) => OUTCOME_TEXT[name].includes(matched));

// Hue-blind on purpose: special woods are hued, and they count toward the pack all the same
export const isLog = (item: Item): boolean => LOG_GRAPHICS.has(item.graphic);

// Recursing through this rather than through logTotal itself: a plain item has no `contents`, and
// passing undefined back into a defaulted parameter would restart at the backpack forever.
const totalIn = (contents: Item[] | undefined): number =>
  (contents ?? []).reduce(
    (total, item) => total + (isLog(item) ? item.amount ?? 1 : 0) + totalIn(item.contents),
    0,
  );

export const logTotal = (contents: Item[] | undefined = player.backpack?.contents): number =>
  totalIn(contents);

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

// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has always had a default for it, so the maybe is kept rather than asserted away
export const chopOnce = (tree: Tree, serial: number | undefined): ChopOutcome | undefined => {
  // A cursor left open by the previous swing would swallow this one
  target.cancel();

  const logsBefore = logTotal();
  journal.clear();

  player.useItemInHand();

  if (!target.wait(TARGET_TIMEOUT)) {
    target.cancel();
    log('chopOnce: no target cursor, nothing usable in hand?');
    return 'noCursor';
  }

  // The graphic is not optional here: target.terrain without one targets the land tile under the
  // tree, which the shard answers with a mining message rather than a chop.
  target.terrain(tree.x, tree.y, tree.z, tree.graphic);

  // author is left undefined on purpose: a shard may route harvest text through the axe as object
  // text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CHOP_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(serial, logsBefore);
};
