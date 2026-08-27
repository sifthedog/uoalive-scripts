import { outcomeVocabulary } from '../lib/outcomes.js';
import { CARVE_TIMEOUT, NO_CURSOR_READ, OUTCOME_TEXT, TARGET_TIMEOUT } from './config.js';

export type Outcome = keyof typeof OUTCOME_TEXT;
export type CarveOutcome = Outcome | 'noCursor' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// The commonest reason a shard declines an action is that it refused outright and said so, and the
// journal has been clear since immediately before the use.
const refusedOutcome = (): CarveOutcome | undefined => {
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, NO_CURSOR_READ);

  return matched ? outcomeFor(matched) : 'noCursor';
};

// There is no silent proof to fall back on the way a chop counts its logs: feathers land in the pack
// on one shard and stay on the corpse on the next, so a pack diff argues for neither.
export const carveOnce = (corpse: Item, knifeSerial: number): CarveOutcome | undefined => {
  target.clearQueue();

  // Cancelled only when there is one to cancel: an unconditional cancel shortly before the action
  // leaves target.open false for the cursor that follows, the same fix dig.ts and boards.ts carry.
  if (target.open) {
    target.cancel();
  }

  journal.clear();
  player.use(knifeSerial);

  if (!target.waitTargetEntity(corpse.serial, TARGET_TIMEOUT)) {
    target.cancel();

    return refusedOutcome();
  }

  // author is left undefined on purpose: a shard may route the result through the knife as object
  // text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CARVE_TIMEOUT);

  return matched ? outcomeFor(matched) : 'unknown';
};
