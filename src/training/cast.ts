import { outcomeVocabulary } from '../lib/outcomes.js';
import type { Stage } from '../lib/stages.js';
import { CAST_TIMEOUT, OUTCOME_TEXT, SKIP_WHEN_BUFFED } from './config.js';

// The outcomes the shard words itself, plus the one the buff gate answers before a cast is even sent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type CastOutcome = Outcome | 'alreadyUp';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

const buffUp = (stage: Stage): boolean =>
  stage.buff !== undefined && player.hasBuffDebuff(stage.buff);

// digOnce reads the pack when the journal stays silent; this reads the two things about a cast that
// do not depend on wording. The success cliloc for an ability differs from shard to shard and is the
// least trustworthy thing here, so unlike the harvest scripts the journal's real job in this module
// is to explain failures - the proof of success is these.
//
// Both are measured against a snapshot taken before the cast. A buff already standing proves nothing
// about this cast, so what counts is the transition; mana can only fall by being spent, which is the
// only proof a stage with no buff of its own has.
//
// With SKIP_WHEN_BUFFED off the run recasts into its own standing buff, so the transition test cannot
// fire for most casts and the mana test is what carries them. That is the more reliable of the two
// anyway - it is the shard charging for the cast it accepted.
const silentOutcome = (
  stage: Stage,
  upBefore: boolean,
  manaBefore: number,
): CastOutcome | undefined => {
  if (!upBefore && buffUp(stage)) {
    return 'cast';
  }

  if (player.mana < manaBefore) {
    return 'cast';
  }

  return undefined;
};

// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has a default for it, so the maybe is kept rather than asserted away.
export const castOnce = (stage: Stage): CastOutcome | undefined => {
  const upBefore = buffUp(stage);

  // Only where the shard treats these as toggles, and this one does not - see SKIP_WHEN_BUFFED. Where
  // it is on, an ability already standing is left alone, because casting it again there would turn
  // the move back off and leave the run alternating on and off forever.
  if (SKIP_WHEN_BUFFED && upBefore) {
    return 'alreadyUp';
  }

  const manaBefore = player.mana;

  journal.clear();
  player.cast(stage.spell);

  // author is left undefined on purpose, for the reason digOnce gives: a shard may route ability text
  // as object text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CAST_TIMEOUT);

  if (matched) {
    return outcomeFor(matched);
  }

  return silentOutcome(stage, upBefore, manaBefore);
};
