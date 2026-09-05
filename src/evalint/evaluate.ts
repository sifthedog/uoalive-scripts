import { outcomeVocabulary } from '../lib/outcomes.js';
import { EVAL_TIMEOUT, OUTCOME_TEXT } from './config.js';

export type EvalOutcome = keyof typeof OUTCOME_TEXT | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// The outcomes no amount of retrying gets past, and what the run says about each
export const STOP_REASON: Partial<Record<EvalOutcome, string>> = {
  unskilled: 'the shard says this character cannot evaluate intelligence',
};

export const evaluateOnce = (): EvalOutcome => {
  target.clearQueue();

  // Cancelled only when there is one to cancel: an unconditional cancel left target.open false for
  // the cursor that followed, in the mining run this was copied from
  if (target.open) {
    target.cancel();
  }

  journal.clear();

  // Targeted in the one call rather than through a cursor of its own: a cursor left unanswered
  // leaves the next cycle asking while the shard is still resolving this attempt
  player.useSkill(Skills.EvalInt, player.serial);

  // author left undefined on purpose: a shard may route the result over the head as object text
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, EVAL_TIMEOUT);

  return matched ? (outcomeFor(matched) ?? 'unknown') : 'unknown';
};
