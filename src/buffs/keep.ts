import { createCaster } from '../lib/cast.js';
import { now } from '../lib/clock.js';
import { spellName } from '../lib/stages.js';
import { CAST_TIMEOUT, KEEP, OUTCOME_TEXT, type Keep } from './config.js';

export interface Kept {
  entry: Keep;
  name: string;

  // Casts in a row the shard said nothing readable about
  misses: number;

  // Not tried again before this
  until: number;

  // Set aside for the rest of the run, and why
  retired?: string;
}

// skipWhenBuffed, unlike the trainers': re-issuing a buff that is already standing is the one thing
// this script exists not to do.
export const { allText, castOnce, outcomeFor } = /* @__PURE__ */ createCaster({
  outcomeText: OUTCOME_TEXT,
  timeoutMs: CAST_TIMEOUT,
  skipWhenBuffed: true,
});

export const roster = (): Kept[] =>
  KEEP.map((entry) => ({ entry, name: spellName(entry.spell), misses: 0, until: 0 }));

export const standing = (entry: Keep): boolean => player.hasBuffDebuff(entry.buff);

// Either hand: a katana is one-handed and a no-dachi two-handed, and Consecrate Weapon takes both
export const armed = (): boolean =>
  (player.equippedItems.twoHanded ?? player.equippedItems.oneHanded) !== undefined;

export const due = (item: Kept): boolean => item.retired === undefined && now() >= item.until;

export const setAside = (item: Kept, forMs: number): void => {
  item.misses = 0;
  item.until = now() + forMs;
};

export const retire = (item: Kept, why: string): void => {
  item.retired = why;
};

// The run has nothing left to do: every entry refused for a reason no later pass can change
export const spent = (roster: Kept[]): boolean => roster.every((item) => item.retired !== undefined);

// What a KEEP_UP=false run waits for. A retired entry counts as settled or it would never finish.
export const settled = (roster: Kept[]): boolean =>
  roster.every((item) => item.retired !== undefined || standing(item.entry));
