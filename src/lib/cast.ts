// One cast, and what the shard made of it. The buckets are a closed set rather than whatever keys a
// folder's OUTCOME_TEXT happens to have, because the loop that switches on them is shared.

import { outcomeVocabulary } from './outcomes.js';
import type { Stage } from './stages.js';

export type CastOutcome =
  // Read from the words, or - more reliably - from the mana and the buff. See silentOutcome.
  | 'cast'

  // A failed casting roll: ordinary, commoner the lower the skill is, and charged for by nobody
  | 'fizzled'

  // The loop gathers mana before it casts, so this means the stage's mana figure is understated
  | 'noMana'

  | 'noReagents'

  // Chivalry's other currency: tithing points, given as gold at a shrine. Nothing a script does
  // refills them either.
  | 'noTithing'

  // Only reached with skipWhenBuffed on, or where the shard says so
  | 'alreadyUp'

  // A wasted cast where these are moves that stack, and the ordinary way out of a form where they
  // are transformations - which is why the loop is told which
  | 'disabled'

  | 'noWeapon'

  // The shard refusing to cast at all because of the form the character is in. Necromancy's Horrific
  // Beast is the one that does this.
  | 'formLocked'

  | 'unskilled'
  | 'saving'

  // The ability's own timer, which is it working as designed
  | 'cooldown'

  // The shard's action throttle, which is not
  | 'throttled'

  // This loop asking again before the shard has finished with the question
  | 'alreadyCasting';

// Partial, so a folder writes down only the outcomes its shard can produce. An absent bucket
// contributes no phrases and can never match.
//
// Key order still decides between two phrases close enough that both match - outcomeVocabulary
// flattens the values in the order they are written - so a table listing `cooldown` before
// `throttled` wins that tie the way it means to.
export type OutcomeText = Partial<Record<CastOutcome, string[]>>;

export interface CasterOptions {
  outcomeText: OutcomeText;

  // The default for a row that does not carry its own castTimeout
  timeoutMs: number;

  // Only right where the shard treats these as toggles; where it does not, gating on the buff caps
  // the run at one cast per buff duration, which is most of its throughput.
  skipWhenBuffed: boolean;
}

export interface Caster {
  allText: string[];
  outcomeFor: (matched: string) => CastOutcome | undefined;
  castOnce: (stage: Stage) => CastOutcome | undefined;
}

const buffUp = (stage: Stage): boolean =>
  stage.buff !== undefined && player.hasBuffDebuff(stage.buff);

// Nothing here opens a cursor and leaves it open: an unanswered target cursor is the state that
// makes every later action in the run fail.
const issue = (stage: Stage): void => {
  if (stage.target === 'self') {
    player.castTo(stage.spell, player);

    return;
  }

  player.cast(stage.spell);
};

export const createCaster = ({ outcomeText, timeoutMs, skipWhenBuffed }: CasterOptions): Caster => {
  const { all, outcomeFor } = outcomeVocabulary(outcomeText);

  // The two things about a cast that do not depend on wording. The success cliloc for an ability
  // differs from shard to shard, so the journal's real job here is to explain failures.
  //
  // Both are measured against a snapshot taken before the cast: a buff already standing proves
  // nothing about this cast, so what counts is the transition, while mana can only fall by being
  // spent - which is the only proof a stage with no buff of its own has.
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

  return {
    allText: all,
    outcomeFor,

    // outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given -
    // but the caller's switch has a default for it, so the maybe is kept rather than asserted away.
    castOnce: (stage) => {
      const upBefore = buffUp(stage);

      if (skipWhenBuffed && upBefore) {
        return 'alreadyUp';
      }

      const manaBefore = player.mana;

      // A cursor left open by anything before this would swallow the answer castTo queues for a
      // self-targeted row, and the row after it would then be cast at nothing.
      target.cancel();

      journal.clear();
      issue(stage);

      // author is left undefined on purpose: a shard may route spell text as object text rather than
      // as System, and a wrong author turns every wait into a timeout.
      const matched = journal.waitForTextAny(all, undefined, stage.castTimeout ?? timeoutMs);

      if (matched) {
        return outcomeFor(matched);
      }

      return silentOutcome(stage, upBefore, manaBefore);
    },
  };
};
