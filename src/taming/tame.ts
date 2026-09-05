import { isMobile } from '../lib/entity.js';
import { outcomeVocabulary } from '../lib/outcomes.js';
import {
  OUTCOME_TEXT,
  TAME_RESOLVE_TIMEOUT,
  TAME_START_TIMEOUT,
  TAME_WAIT_SLICE,
} from './config.js';

export type Outcome = keyof typeof OUTCOME_TEXT;

// 'pending' is an attempt the shard accepted and never resolved inside the budget
export type TameOutcome = Outcome | 'pending' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// The start line is still in the journal when the second wait goes out, so waiting on the full list
// would match it again and spin. Filtered rather than cleared: a second journal.clear() can throw
// away a resolution that landed in the same tick.
export const RESOLUTION_TEXT: string[] = ALL_OUTCOME_TEXT.filter(
  (text) => !OUTCOME_TEXT.starting.includes(text),
);

// The outcomes no amount of retrying gets past, and what the run says about each
export const STOP_REASON: Partial<Record<TameOutcome, string>> = {
  hopeless: 'the shard says this creature cannot be tamed by you',
  notAnimal: 'that is not something Animal Taming works on',
  alreadyTame: 'that animal is already tame',
  unskilled: 'not skilled enough to tame this creature',
};

// isRenamable is true for pets and followers, and is how lib/threat.ts tells your own pet from a
// stranger's
const renamable = (serial: number): boolean => {
  const found = client.findObject(serial);

  return !!found && isMobile(found) && found.isRenamable;
};

// Taken in slices so the caller gets a turn between them. A line that landed during one is still
// matched by the next: waitForTextAny reads the journal as it stands, which is the same property the
// two-stage wait already relies on.
//
// author is left undefined on purpose: the shard routes the taming lines over the creature's head as
// object text, and a wrong author turns every wait into a timeout
const waitOut = (texts: string[], budgetMs: number, between?: () => void): string | null => {
  for (let waited = 0; waited < budgetMs; waited += TAME_WAIT_SLICE) {
    const matched = journal.waitForTextAny(texts, undefined, TAME_WAIT_SLICE);

    if (matched) {
      return matched;
    }

    between?.();
  }

  return null;
};

const settle = (serial: number, wasPet: boolean, between?: () => void): TameOutcome => {
  const opened = waitOut(ALL_OUTCOME_TEXT, TAME_START_TIMEOUT, between);
  const first = opened ? (outcomeFor(opened) ?? 'unknown') : undefined;

  if (first && first !== 'starting') {
    return first;
  }

  const settled = waitOut(RESOLUTION_TEXT, TAME_RESOLVE_TIMEOUT, between);

  if (settled) {
    return outcomeFor(settled) ?? 'unknown';
  }

  // Silence is what a shard with other wordings looks like, so the flag is the proof that does not
  // go through the journal - false to true, since one already renamable proves nothing here
  if (!wasPet && renamable(serial)) {
    return 'tamed';
  }

  return first === 'starting' ? 'pending' : 'unknown';
};

export const tameOnce = (serial: number, between?: () => void): TameOutcome => {
  target.clearQueue();

  // Cancelled only when there is one to cancel: an unconditional cancel just before an action left
  // target.open false for the cursor that followed, in the mining run this was copied from
  if (target.open) {
    target.cancel();
  }

  const wasPet = renamable(serial);

  journal.clear();

  // Targeted in the one call rather than through a cursor of its own: a cursor left unanswered is
  // what leaves the next cycle asking while the shard is still resolving this attempt.
  player.useSkill(Skills.AnimalTaming, serial);

  return settle(serial, wasPet, between);
};
