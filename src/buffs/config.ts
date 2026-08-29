import type { Castable, OutcomeText } from '../lib/cast.js';
import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export {
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

export interface Keep extends Castable {
  // Required where Stage leaves it optional: a spell the client publishes no buff for cannot be told
  // apart from one that never went up, and the run would recast it every pass forever.
  buff: BuffDebuffs;

  // A ceiling rather than a price: the shard charges a paladin less as Chivalry rises
  mana: number;

  // Consecrate Weapon enchants what is in hand and is refused with an empty one
  needsWeapon?: boolean;
}

// Cast in this order within a pass.
export const KEEP: Keep[] = [
  {
    spell: Spells.ConsecrateWeapon,
    buff: BuffDebuffs.ConsecrateWeapon,
    mana: 10,
    needsWeapon: true,
  },

  { spell: Spells.DivineFury, buff: BuffDebuffs.DivineFury, mana: 15 },
];

// Between passes. The buff bar is fed by server packets, so this is how stale the run's picture of
// it can be, and roughly how long a lapsed buff stays down.
export const POLL = 1000;

// Long enough for the buff packet to land after the incantation, which is what a shard that words
// these differently is read by
export const CAST_TIMEOUT = 1000;

// Between two casts inside one pass, to stay under the action throttle
export const CAST_DELAY = 600;

// Consecutive casts the shard said nothing readable about, and that put no buff up and spent no
// mana, before the entry is set aside
export const MAX_MISSES = 5;

// How long an entry refused for something a pass cannot fix - no weapon, no cursor of its own making
// - is left alone before it is tried again
export const SET_ASIDE = 60_000;

// Runs for a day at POLL. A keeper standing over a character with both buffs up is working, so
// nothing here counts cycles against it.
export const MAX_CYCLES = 100_000;

// Off is a keeper that puts the buffs up and stops. On it keeps them up until you stop the script.
export const KEEP_UP = true;

// Guesses, apart from the tithing wording. Correct them against the real journal after the first
// run: a phrase that never matches shows up as a miss, not as a silent wrong turn.
export const OUTCOME_TEXT: OutcomeText = {
  // Not depended on: the buff arriving and the mana leaving the pool are the proof
  cast: ['Your weapon is consecrated', 'You are filled with divine fury'],

  fizzled: ['You fail to cast the spell', 'The spell fizzles'],

  noTithing: [
    'You do not have enough tithing points',
    'You must have at least',
    'You need to make an offering',
  ],

  noMana: ['You do not have enough mana', 'Insufficient mana'],

  alreadyUp: ['You are already under the effect'],

  noWeapon: [
    'You cannot consecrate your fists',
    'You must have a weapon',
    'You must be wielding a weapon',
  ],

  unskilled: ['You are not pious enough', 'Your karma is not high enough', ...UNSKILLED_TEXT],

  saving: SAVING_TEXT,

  // Before throttled: waitForTextAny hands back whichever string it found, and THROTTLED_TEXT ends
  // in a bare 'You must wait' that a longer sentence can contain.
  alreadyCasting: ['You are already casting a spell', 'You are already casting'],

  throttled: THROTTLED_TEXT,
};
