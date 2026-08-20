import { outcomeVocabulary } from '../lib/outcomes.js';
import { HIDE_TEXT, HIDE_TIMEOUT } from './config.js';

export type HideOutcome = keyof typeof HIDE_TEXT | 'unknown';

export const { all: ALL_HIDE_TEXT, outcomeFor } = outcomeVocabulary(HIDE_TEXT);

// Using the skill while already hidden rolls it again, so the run never has to reveal itself first
export const hideOnce = (): HideOutcome => {
  const before = player.isHidden;

  journal.clear();

  // author is left undefined on purpose: a shard may route this over the character's head as object text
  player.useSkill(Skills.Hiding);

  const matched = journal.waitForTextAny(ALL_HIDE_TEXT, undefined, HIDE_TIMEOUT);

  if (matched) {
    return outcomeFor(matched) ?? 'unknown';
  }

  // Silence is what a shard with other wordings looks like, so the client's own flag is the proof
  // that does not go through the journal - false to true, since already hidden proves nothing here.
  return !before && player.isHidden ? 'hidden' : 'unknown';
};
