import { queryOPL } from '../lib/opl.js';
import {
  METAL_ASKS,
  METAL_MISSES,
  NOT_METAL_TEXT,
  OPL_TIMEOUT,
  ORE_METALS,
  ORE_METAL_LINE,
} from './config.js';

// A tooltip that answers with no metal line is plain iron, and it has to key the same as one that
// says 'Iron' or two piles of the one metal sit apart for the whole run.
const PLAIN = 'iron';

// Answers only. A miss is deliberately not kept: the pile a swing just delivered has usually not been
// sent its tooltip yet, and caching that for the pile's life left it unnamed for good - which is what
// put it in nextPair's last-resort pairing and earned a refusal every cycle.
const metals = new Map<number, string>();

// Asked and unanswered this pass, so an unnamed pile costs one lookup a pass rather than one a read
const missedThisPass = new Set<number>();

// Lookups spent per serial, so a pile the shard will never name stops costing OPL_TIMEOUT a pass
const asks = new Map<number, number>();

// A metal the shard then refused against itself, so the line being read is not the metal after all
const doubted = new Set<string>();

let oplNamesMetals = true;
let misses = 0;

// A shard that has never answered one is not keeping a pile waiting for the next: without this, a
// shard with no OPL at all deferred every pair until the miss latch tripped.
let oplAnswered = false;

// Same shape peek.ts and tool.ts read their lines out of: the property text and its values, joined
const textOf = (property: { text?: string; values?: { text?: string }[] }): string => {
  const values = (property.values ?? []).map((value) => value.text ?? '').join(' ');

  return `${property.text ?? ''} ${values}`.trim();
};

const readMetal = (name: string, properties: { text?: string }[]): string => {
  const lines = properties.map(textOf).filter((line) => line && line !== name);

  const known = lines.find((line) => ORE_METALS.has(line.toLowerCase()));

  if (known) {
    return known.toLowerCase();
  }

  const learned = lines.find((line) => ORE_METAL_LINE.test(line) && !NOT_METAL_TEXT.test(line));

  if (!learned) {
    return PLAIN;
  }

  ORE_METALS.add(learned.toLowerCase());
  log(`ore: '${learned}' is a metal too, remembering it`);

  return learned.toLowerCase();
};

const worthAsking = (serial: number): boolean =>
  oplNamesMetals && !missedThisPass.has(serial) && (asks.get(serial) ?? 0) < METAL_ASKS;

const lookUp = (serial: number): void => {
  if (metals.has(serial) || !worthAsking(serial)) {
    return;
  }

  asks.set(serial, (asks.get(serial) ?? 0) + 1);

  const opl = queryOPL(serial, OPL_TIMEOUT, 'ore');
  const properties = opl?.properties ?? [];

  if (properties.length === 0) {
    missedThisPass.add(serial);
    misses += 1;

    if (misses >= METAL_MISSES) {
      oplNamesMetals = false;
      log('ore: tooltips are not naming the metal here, so a pair has to be refused to be split');
    }

    return;
  }

  misses = 0;
  oplAnswered = true;
  metals.set(serial, readMetal(opl?.name ?? '', properties));
};

// undefined is 'the tooltip did not say', which is not a metal of its own: callers fall back to the
// hue and the shard's refusal for those.
export const metalOf = (item: Item): string | undefined => {
  lookUp(item.serial);

  const metal = metals.get(item.serial);

  return metal !== undefined && doubted.has(metal) ? undefined : metal;
};

// Still worth waiting a pass for. Pairing on a guess is what earns the refusal, and the pile the
// swing just landed has its metal by the next pass.
export const metalPending = (item: Item): boolean => {
  lookUp(item.serial);

  // Not worthAsking: a pile that missed *this* pass is still pending, or it would be paired on a
  // guess the moment its lookup came back empty.
  return (
    oplAnswered &&
    oplNamesMetals &&
    !metals.has(item.serial) &&
    (asks.get(item.serial) ?? 0) < METAL_ASKS
  );
};

// Cleared per grouping pass, not per run: a miss is as likely to be a tooltip still in flight as a
// shard that will never name this pile.
export const startMetalPass = (): void => {
  missedThisPass.clear();
};

export const doubtMetal = (metal: string): void => {
  if (doubted.has(metal)) {
    return;
  }

  doubted.add(metal);
  log(`ore: the shard refused two piles both read as '${metal}', so that line is not the metal`);
};

// The shard reissues the serial of a pile a combine or a smelt consumed, so a stale entry would name
// the wrong metal for whatever turns up wearing it next.
export const forgetMissingMetals = (piles: Item[]): void => {
  const here = new Set(piles.map((pile) => pile.serial));

  for (const serial of [...metals.keys()]) {
    if (!here.has(serial)) {
      metals.delete(serial);
    }
  }

  for (const serial of [...asks.keys()]) {
    if (!here.has(serial)) {
      asks.delete(serial);
    }
  }
};
