import { distanceTo, hex } from '../lib/entity.js';
import { queryOPL } from '../lib/opl.js';
import { CORPSE_GRAPHIC, CORPSE_PREFIX } from './config.js';

export interface Candidate {
  serial: number;
  // '' when neither the tooltip nor the object would say, which is the normal state for a ghost
  name: string;
  distance: number;
}

export type Match = 'exact' | 'loose';

export interface Choice {
  picked: Candidate;
  why: Match | 'nearest';
  named: number;
}

// No container filter, unlike the floor sweep: a corpse is never inside anything. graphic reads 0
// for an entity the client is no longer tracking.
export const onGround = (): Item[] =>
  client.findAllItemsOfType(CORPSE_GRAPHIC, undefined, 'world').filter((item) => item.graphic !== 0);

export const inRange = (corpses: Item[], range: number): Item[] =>
  corpses.filter((corpse) => distanceTo(corpse) <= range);

export const nearest = (corpses: Item[]): number | undefined =>
  corpses.reduce<number | undefined>(
    (best, corpse) => Math.min(distanceTo(corpse), best ?? Infinity),
    undefined,
  );

// Sorted before the asks are capped, so they are spent on the corpses most likely to be yours. Only
// the nameless ones are worth OPL_TIMEOUT: the rest name themselves.
export const survey = (corpses: Item[], asks: number, oplTimeout: number): Candidate[] => {
  const sorted = [...corpses].sort((a, b) => distanceTo(a) - distanceTo(b));

  let spent = 0;

  return sorted.map((corpse) => {
    let name = (corpse.name ?? '').trim();

    if (!name && spent < asks) {
      spent++;
      name = (queryOPL(corpse.serial, oplTimeout, 'corpse')?.name ?? '').trim();
    }

    return { serial: corpse.serial, name, distance: distanceTo(corpse) };
  });
};

const words = (text: string): string[] =>
  text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);

// Split rather than matched with a regex, so a player name never has to be escaped
const hasWord = (text: string, word: string): boolean => words(text).includes(word);

export const matchOf = (name: string, playerName: string): Match | undefined => {
  const corpse = name.trim().toLowerCase();
  const me = playerName.trim().toLowerCase();

  // Either side empty matches nothing: a nameless player would otherwise claim every corpse
  if (!corpse || !me) {
    return undefined;
  }

  if (corpse.startsWith(CORPSE_PREFIX) && corpse.slice(CORPSE_PREFIX.length).trim() === me) {
    return 'exact';
  }

  return hasWord(corpse, me) ? 'loose' : undefined;
};

const RANK: Record<Match | 'nearest', number> = { exact: 0, loose: 1, nearest: 2 };

export const chooseMine = (candidates: Candidate[], playerName: string): Choice | undefined => {
  const ranked = candidates
    .map((candidate) => ({
      candidate,
      why: (matchOf(candidate.name, playerName) ?? 'nearest') as Match | 'nearest',
    }))
    .sort((a, b) => RANK[a.why] - RANK[b.why] || a.candidate.distance - b.candidate.distance);

  const best = ranked[0];

  if (!best) {
    return undefined;
  }

  return {
    picked: best.candidate,
    why: best.why,
    named: ranked.filter((one) => one.why !== 'nearest').length,
  };
};

// The census, said once at startup: a wrong CORPSE_GRAPHIC is otherwise a silent 'nothing here'
export const describeGround = (corpses: Item[]): string =>
  `${hex(CORPSE_GRAPHIC)} x${corpses.length}`;
