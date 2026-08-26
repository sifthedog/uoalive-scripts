import { packContents } from '../lib/containers.js';
import { totalMatching } from '../lib/pack.js';
import {
  COMBINE_DELAY,
  COMBINE_POLL,
  COMBINE_TIMEOUT,
  DIFFERENT_ORE_TEXT,
  MAX_COMBINE_ATTEMPTS,
  ORE_GRAPHICS,
  ORE_NAME,
  ORE_SETTLE_POLL,
  ORE_SETTLE_TIMEOUT,
  TARGET_TIMEOUT,
  THROTTLED_TEXT,
} from './config.js';
import {
  doubtMetal,
  forgetMissingMetals,
  metalOf,
  metalPending,
  startMetalPass,
} from './metal.js';

// Named for the item rather than the tile, because vein.ts already owns `isOre` for the ground.
//
// Graphic first, name second: names are empty until the client has tooltip data. The name covers a
// shard whose ore wears an art the seeded set has never heard of, and an art learned that way joins
// the set - so it costs one tooltip and no more.
export const isOrePile = (item: Item): boolean => {
  if (ORE_GRAPHICS.has(item.graphic)) {
    return true;
  }

  if (!ORE_NAME.test(item.name ?? '')) {
    return false;
  }

  ORE_GRAPHICS.add(item.graphic);
  log(`ore: 0x${item.graphic.toString(16)} '${item.name}' is ore too, remembering the art`);

  return true;
};

// Hue-blind on purpose: every ore type counts toward the pack, whatever it smelts into
export const oreTotal = (contents?: Item[]): number => totalMatching(isOrePile, contents);

// Reads the total rather than the number of piles, so a shard that does merge ore on arrival is
// satisfied immediately instead of waiting out the timeout on every swing. False is not a failure
// worth acting on: a pile that arrived late is picked up by the next swing's grouping.
export const waitForOre = (before: number): boolean => {
  for (let waited = 0; waited < ORE_SETTLE_TIMEOUT; waited += ORE_SETTLE_POLL) {
    // Read before the first sleep, unlike convert.ts's waitForChange: the delivery has usually
    // already happened by the time the journal line announcing it is read.
    if (oreTotal() > before) {
      return true;
    }

    sleep(ORE_SETTLE_POLL);
  }

  return false;
};

const amountOf = (item: Item): number => item.amount ?? 1;
const hueOf = (item: Item): number => item.hue ?? 0;
const describe = (item: Item): string =>
  `${amountOf(item)} ${metalOf(item) ?? `hue ${hueOf(item)}`}`;

// Top level only, unlike oreTotal: the combine and the smelt both act by serial on loose items.
// Largest first, so the pile a combine consumes is always the smaller one.
export const orePiles = (): Item[] =>
  (packContents() ?? []).filter(isOrePile).sort((a, b) => amountOf(b) - amountOf(a));

// The backstop for the piles metal.ts could not name. Remembered by serial, which is why it cannot
// carry a run alone: every swing delivers a pile wearing a serial nothing has been learned about.
const differing = new Set<string>();

// This call only: a silent miss is as likely to be a busy moment as a verdict, and remembering it for
// the run would split two piles of one metal for good.
const skipped = new Set<string>();

const serialKey = (a: Item, b: Item): string =>
  a.serial < b.serial ? `s${a.serial}:${b.serial}` : `s${b.serial}:${a.serial}`;

const hueKey = (a: Item, b: Item): string =>
  hueOf(a) < hueOf(b) ? `h${hueOf(a)}:${hueOf(b)}` : `h${hueOf(b)}:${hueOf(a)}`;

// Never for hue 0, which is both iron and 'the client has not said yet'
const hueTellsThemApart = (a: Item, b: Item): boolean =>
  hueOf(a) !== 0 && hueOf(b) !== 0 && hueOf(a) !== hueOf(b);

// Only ever forbids: one pile the tooltip could not name must not split its own metal, so an unknown
// on either side falls through to the hue and the refusal below.
const metalTellsThemApart = (a: Item, b: Item): boolean => {
  const mine = metalOf(a);

  return mine !== undefined && metalOf(b) !== undefined && mine !== metalOf(b);
};

const differs = (a: Item, b: Item): boolean =>
  // A pile whose tooltip is still in flight is paired with nothing at all. Guessing at it is what
  // earned a refusal every cycle, and one more swing loose costs the pack nothing.
  metalPending(a) ||
  metalPending(b) ||
  metalTellsThemApart(a, b) ||
  differing.has(serialKey(a, b)) ||
  skipped.has(serialKey(a, b)) ||
  (hueTellsThemApart(a, b) && differing.has(hueKey(a, b)));

const sameMetal = (a: Item, b: Item): boolean => {
  const mine = metalOf(a);

  return mine !== undefined && mine === metalOf(b);
};

const said = (texts: string[]): boolean => texts.some((text) => journal.containsText(text));

// A merge is silent either way, so the pack is the evidence: the consumed pile gone, or the pile it
// went into grown. The refusal cuts the wait short, or a pack holding two metals spends the whole
// timeout on every swing.
const merged = (primary: Item, dup: Item, before: number): boolean => {
  for (let waited = 0; waited < COMBINE_TIMEOUT; waited += COMBINE_POLL) {
    const piles = packContents() ?? [];
    const grown = piles.find((item) => item.serial === primary.serial);

    if (!piles.some((item) => item.serial === dup.serial) || (grown && amountOf(grown) > before)) {
      return true;
    }

    if (said(DIFFERENT_ORE_TEXT)) {
      return false;
    }

    sleep(COMBINE_POLL);
  }

  return false;
};

const combine = (primary: Item, dup: Item): void => {
  const before = amountOf(primary);

  journal.clear();
  player.use(dup.serial);

  // No cancel before the use: a cursor cancelled shortly before an action has been measured costing
  // that action its own cursor.
  if (!target.waitTargetEntity(primary.serial, TARGET_TIMEOUT)) {
    target.cancel();
    skipped.add(serialKey(primary, dup));
    log(`groupOres: no target cursor for ${describe(dup)}`);

    return;
  }

  if (merged(primary, dup, before)) {
    return;
  }

  // Nothing was attempted, so nothing has been learned about the metals
  if (said(THROTTLED_TEXT)) {
    log('groupOres: the shard says wait, leaving the two of them paired');

    return;
  }

  if (said(DIFFERENT_ORE_TEXT)) {
    const metal = metalOf(primary);

    if (metal !== undefined && metal === metalOf(dup)) {
      doubtMetal(metal);
    }

    differing.add(serialKey(primary, dup));

    if (hueTellsThemApart(primary, dup)) {
      differing.add(hueKey(primary, dup));
    }

    return;
  }

  skipped.add(serialKey(primary, dup));
  log(`groupOres: ${describe(primary)} and ${describe(dup)} did not merge and nothing was said`);
};

// The first pile that can join one already seen, largest first. Everything ahead of it is a family of
// its own, so returning nothing means every pile in the pack is a metal of its own.
const nextPair = (piles: Item[]): [Item, Item] | undefined => {
  const primaries: Item[] = [];

  for (const pile of piles) {
    // The tooltip's metal first, then hue: hue is right nearly always, and wrong costs a refusal
    const home =
      primaries.find((primary) => sameMetal(primary, pile) && !differs(primary, pile)) ??
      primaries.find((primary) => hueOf(primary) === hueOf(pile) && !differs(primary, pile)) ??
      primaries.find((primary) => !differs(primary, pile));

    if (home) {
      return [home, pile];
    }

    primaries.push(pile);
  }

  return undefined;
};

export const groupOres = (): void => {
  skipped.clear();
  startMetalPass();

  for (let attempt = 0; attempt < MAX_COMBINE_ATTEMPTS; attempt++) {
    const piles = orePiles();
    forgetMissingMetals(piles);

    const pair = nextPair(piles);

    if (!pair) {
      if (skipped.size > 0 && piles.length > 1) {
        log(`groupOres: left ${piles.length} piles - ${piles.map(describe).join(', ')}`);
      }

      return;
    }

    combine(pair[0], pair[1]);
    sleep(COMBINE_DELAY);
  }

  log(`groupOres: hit the ${MAX_COMBINE_ATTEMPTS} attempt backstop`);
};
