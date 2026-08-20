import { outcomeVocabulary } from '../lib/outcomes.js';
import { STEALTH_TEXT, STEALTH_TIMEOUT } from './config.js';

export type StealthOutcome = keyof typeof STEALTH_TEXT | 'unknown';

export const { all: ALL_STEALTH_TEXT, outcomeFor } = outcomeVocabulary(STEALTH_TEXT);

export const stealthOnce = (): StealthOutcome => {
  const before = player.isHidden;

  journal.clear();

  // author is left undefined on purpose: a shard may route this over the character's head as object text
  player.useSkill(Skills.Stealth);

  const matched = journal.waitForTextAny(ALL_STEALTH_TEXT, undefined, STEALTH_TIMEOUT);

  if (matched) {
    return outcomeFor(matched) ?? 'unknown';
  }

  // A refusal leaves you hidden, so standing still only the flag going down proves the attempt rolled and lost
  return before && !player.isHidden ? 'failed' : 'unknown';
};
