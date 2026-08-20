import { hex } from '../lib/entity.js';
import { outcomeVocabulary } from '../lib/outcomes.js';
import {
  NO_CURSOR_READ,
  OUTCOME_TEXT,
  PICK_TIMEOUT,
  POKE_BOX,
  POKE_DELAY,
  TARGET_TIMEOUT,
} from './config.js';
import { lockpickTotal } from './picks.js';

export type Outcome = keyof typeof OUTCOME_TEXT;
export type PickOutcome = Outcome | 'noCursor' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// The outcomes no amount of retrying gets past, and what the run says about each
export const STOP_REASON: Partial<Record<PickOutcome, string>> = {
  picked: 'the lock is open - a box that will not lock again cannot train anything',
  tooHard: 'the shard says this lock is beyond you',
  notLocked: 'that container is not locked',
  tooFar: 'stand next to the container',
  noPicks: 'out of lockpicks',
};

// A shard that words its lockpicking differently leaves the journal silent, so read the pack: only a
// broken pick changes the count, and a stack keeps its serial while its amount drops.
const silentOutcome = (before: number): PickOutcome =>
  lockpickTotal() < before ? 'broke' : 'unknown';

// No cursor is not the same as nothing having happened: the commonest reason is a refusal the shard
// already said, and the journal has been clear since immediately before the click.
const refusedOutcome = (boxSerial: number, before: number): PickOutcome | undefined => {
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, NO_CURSOR_READ);
  if (matched) {
    return outcomeFor(matched);
  }

  const silent = silentOutcome(before);
  if (silent !== 'unknown') {
    return silent;
  }

  log(`pickOnce: no target cursor for ${hex(boxSerial)} - is the lockpick still in the pack?`);

  return 'noCursor';
};

// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has a default for it, so the maybe is kept rather than asserted away
export const pickOnce = (boxSerial: number, lockpickSerial: number): PickOutcome | undefined => {
  target.clearQueue();

  // Cancelled only when there is one to cancel: an unconditional cancel just before an action left
  // target.open false for the cursor that followed
  if (target.open) {
    target.cancel();
  }

  if (POKE_BOX) {
    player.use(boxSerial);
    sleep(POKE_DELAY);
  }

  const before = lockpickTotal();

  // After the poke, so its own 'this is locked' line is not read as the attempt's outcome
  journal.clear();

  player.use(lockpickSerial);

  if (!target.waitTargetEntity(boxSerial, TARGET_TIMEOUT)) {
    target.cancel();
    return refusedOutcome(boxSerial, before);
  }

  // author is left undefined on purpose: a shard may route this through the lockpick as object text
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, PICK_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(before);
};
