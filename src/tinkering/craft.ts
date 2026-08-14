import {
  CRAFT_TIMEOUT,
  GUMP_POLL,
  GUMP_TIMEOUT,
  NEXT_PAGE_BUTTON,
  OUTCOME_TEXT,
  type CalibratedRecipe,
} from './config.js';
import { craftGump, openCraftGump, pageWith } from './gump.js';
import { ingotTotal } from './ingots.js';
import { toolAlive } from './tool.js';

// The outcomes the shard words itself, plus the ones the world is read for when it stays silent
export type Outcome = keyof typeof OUTCOME_TEXT;
export type CraftOutcome = Outcome | 'used' | 'unknown' | 'noGump';

export const ALL_OUTCOME_TEXT = Object.values(OUTCOME_TEXT).flat();

export const outcomeFor = (matched: string): Outcome | undefined =>
  (Object.keys(OUTCOME_TEXT) as Outcome[]).find((name) => OUTCOME_TEXT[name].includes(matched));

// Stock RunUO renders craft results inside the reopened craft gump, not as a system message, so
// the journal may stay silent on every cycle. Read the world instead: ingots leave the pack on a
// success and on a lossy failure alike, and the loop treats those two the same.
const silentOutcome = (toolSerial: number, ingotsBefore: number): CraftOutcome => {
  if (!toolAlive(toolSerial)) {
    return 'wornOut';
  }

  const after = ingotTotal();
  if (after < ingotsBefore) {
    return 'used';
  }
  if (after === 0) {
    return 'noMaterial';
  }

  return 'unknown';
};

// outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given - but
// the caller's switch has always had a default for it, so the maybe is kept rather than asserted away
export const craftOnce = (
  recipe: CalibratedRecipe,
  toolSerial: number,
): CraftOutcome | undefined => {
  const categoryPage = openCraftGump(toolSerial, recipe.category);
  if (!categoryPage) {
    return 'noGump';
  }

  categoryPage.reply(recipe.category);

  // The selections pane shows ten rows at a time, and an item further down needs NEXT PAGE first.
  // Item buttons repeat per page, so paging is counted rather than detected.
  const nextPage = NEXT_PAGE_BUTTON;
  const hops = recipe.nextPages ?? 0;

  // A recipe that needs paging with no button to page by cannot be reached at all, and pressing an
  // unidentified button to find out is exactly what the probe exists to avoid.
  if (hops > 0 && nextPage === undefined) {
    log('craftOnce: this recipe needs NEXT PAGE, but NEXT_PAGE_BUTTON is unset in config.ts');
    return 'noGump';
  }

  for (let hop = 0; hop < hops && nextPage !== undefined; hop++) {
    const before = craftGump();
    if (!before) {
      return 'noGump';
    }
    before.reply(nextPage);
    sleep(GUMP_POLL);
  }

  const itemPage = pageWith(recipe.item, GUMP_TIMEOUT);
  if (!itemPage) {
    return 'noGump';
  }

  const ingotsBefore = ingotTotal();
  journal.clear();
  itemPage.reply(recipe.item);

  // author is left undefined on purpose: a shard may route craft text through the tool as object
  // text rather than as System, and a wrong author turns every wait into a timeout.
  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CRAFT_TIMEOUT);

  return matched ? outcomeFor(matched) : silentOutcome(toolSerial, ingotsBefore);
};
