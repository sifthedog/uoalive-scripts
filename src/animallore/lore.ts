import { outcomeVocabulary } from '../lib/outcomes.js';
import { LORE_GUMP_TEXT, LORE_POLL, LORE_TIMEOUT, OUTCOME_TEXT } from './config.js';
import { closeLoreGump } from './gump.js';

export type Outcome = keyof typeof OUTCOME_TEXT;

// 'lored' has no wording of its own because the shard has none: a read that works opens the gump and
// says nothing at all.
export type LoreOutcome = Outcome | 'lored' | 'unknown';

export const { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

// The outcomes no amount of retrying gets past, and what the run says about each
export const STOP_REASON: Partial<Record<LoreOutcome, string>> = {
  notAnimal: 'that is not something Animal Lore reads',
  notYours: 'the shard only lores tamed creatures',
  unskilled: 'not skilled enough to lore this creature',
};

// The gump is checked first and the journal second, because success is the common case and the
// silent one. findOrWait's own timeout is the poll, so there is no sleep of its own here.
const settled = (): { said?: string; opened: boolean } => {
  for (let waited = 0; waited < LORE_TIMEOUT; waited += LORE_POLL) {
    const gump = Gump.findOrWait(LORE_GUMP_TEXT, LORE_POLL);

    if (gump) {
      closeLoreGump(gump);

      return { opened: true };
    }

    const said = ALL_OUTCOME_TEXT.find((text) => journal.containsText(text));

    if (said) {
      return { said, opened: false };
    }
  }

  return { opened: false };
};

export const loreOnce = (serial: number): LoreOutcome => {
  target.clearQueue();

  // Cancelled only when there is one to cancel: an unconditional cancel just before an action left
  // target.open false for the cursor that followed, in the mining run this was copied from
  if (target.open) {
    target.cancel();
  }

  journal.clear();

  // Targeted in the one call rather than through a cursor of its own. A cursor left unanswered is
  // what leaves the next cycle asking again while the shard is still waiting on this one, and a loop
  // that does that re-arms the skill timer faster than it expires.
  player.useSkill(Skills.AnimalLore, serial);

  const { said, opened } = settled();

  if (said) {
    return outcomeFor(said) ?? 'unknown';
  }

  return opened ? 'lored' : 'unknown';
};
