// Re-exported rather than imported directly so this file stays the only one consumers import.
export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  SAVE_DONE_TEXT,
  SAVE_POLL,
  SAVE_WAIT,
  SAVING_TEXT,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

// STALL_WARN and STALL_STOP are left out: a cycle counter reads a character meditating on purpose
// as a run that has stopped getting anywhere.

import type { OutcomeText } from '../lib/cast.js';
import type { Layer } from '../lib/gear.js';
import type { MeditateText } from '../lib/meditate.js';
import type { Stage } from '../lib/stages.js';
import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export const SKILL = Skills.Magery;

// Used in the log lines until the skill list arrives
export const SKILL_LABEL = 'Magery';

// upTo is in the client's tenths - 500 is 50.0 - and exclusive, so the bands butt together.
// These are the spells the usual guides name as gaining without a victim to throw them at: a
// punchbag has to be found, kept alive and kept in range, which is three more ways for a run to end.
export const STAGES: Stage[] = [
  // 3rd circle. Below about 30 the sensible thing is to buy the skill from an NPC trainer.
  { upTo: 500, spell: Spells.Bless, mana: 9, buff: BuffDebuffs.Bless, target: 'self' },

  // 4th circle
  {
    upTo: 650,
    spell: Spells.ArchProtection,
    mana: 11,
    buff: BuffDebuffs.ArchProtection,
    target: 'self',
  },

  // 6th. The 5th and 7th circles are skipped because their spells want a cursor over ground or a
  // gump answered, and neither is something this loop can do.
  { upTo: 850, spell: Spells.Invisibility, mana: 20, buff: BuffDebuffs.Invisibility, target: 'self' },

  // 8th. An area attack that hits everything nearby, so this band belongs somewhere empty.
  { upTo: 1200, spell: Spells.Earthquake, mana: 50 },
];

export const SKILL_TIMEOUT = 1_000;
export const SKILL_POLL = 500;

// Consecutive cycles the client answered nothing for the skill before giving up
export const MAX_BLIND_READS = 5;

// A spell has an incantation to get through, and a refusal arriving after the wait has closed reads
// as an unknown outcome.
export const CAST_TIMEOUT = 2000;

// Pacing, not a wait: an eighth-circle cast is seconds long, and coming back sooner just earns 'you
// are already casting'. The alreadyCasting backoff finds the rest.
export const CAST_DELAY = 3000;

// Gating on the buff would cap the run at one cast per buff duration.
export const SKIP_WHEN_BUFFED = false;

// On, because Protection and Magic Reflection are toggles here: the cast was charged for and the
// skill rolled either way.
export const DISABLED_IS_PROGRESS = true;

export const BUFF_WAIT = 2000;

// Nothing to out-wait but the spell's own casting time
export const CASTING_WAIT = 750;

// Backs off from alreadyCasting; the ceiling is high because the eighth-circle band is the slow one.
export const COOLDOWN_BACKOFF = 2000;
export const COOLDOWN_BACKOFF_MAX = 20_000;

// Off waits for natural regeneration instead: slower, always available.
export const MEDITATE = true;

// The last band charges 50 a cast, so a pool topped right up pays for several casts.
export const MEDITATE_TO_FULL = true;

export const MEDITATE_TIMEOUT = 20_000;
export const MEDITATE_ATTEMPTS = 4;

export const MEDITATE_START_TIMEOUT = 2000;

export const MANA_POLL = 500;
export const MANA_LOG_EVERY = 10_000;

// For a run with MEDITATE off, or one the shard refused
export const REGEN_TIMEOUT = 120_000;

// In the order it comes off, which is also the order it goes back on. Hands first: they are the only
// layers whose absence ends a run. Jewellery is left on - it blocks meditation on no shard this was
// written against, and every layer here is two more item moves on every trance. Add Layers.Necklace
// where a gorget counts as armour; that layer carries both.
export const STRIP_LAYERS: Layer[] = [
  Layers.OneHanded,
  Layers.TwoHanded,
  Layers.Helmet,
  Layers.Gloves,
  Layers.Arms,
  Layers.Torso,
  Layers.Tunic,
  Layers.Legs,
  Layers.Pants,
  Layers.Shirt,
  Layers.Waist,
  Layers.Skirt,
  Layers.Robe,
  Layers.Cloak,
  Layers.Shoes,
];

// Pause between the moves inside one strip, to stay under the action throttle. Too low shows up as
// throttle wording in the journal and a strip that needs its reissue.
export const STRIP_MOVE_DELAY = 500;

// Off, so the run learns from the shard's own refusal whether armour blocks a trance. Turn it on for
// a shard already known to block, to save one refused trance.
export const STRIP_AT_ONCE = false;

// Deliberately not the EQUIP_ trio, though they hold the same numbers today: an equip and a stow are
// independent facts about the shard.
export const DISARM_TIMEOUT = 2000;
export const DISARM_POLL = 200;
export const DISARM_ATTEMPTS = 3;


export const MAX_HUNGRY = 5;

// Guesses - correct them against the real journal after the first run. A phrase that never matches
// shows up as an unknown outcome, not as a silent wrong turn.
export const OUTCOME_TEXT: OutcomeText = {
  // Not depended on: the mana leaving the pool and the buff arriving are the proof
  cast: ['You feel a surge of magic', 'You are now protected'],

  fizzled: ['The spell fizzles', 'You have failed to cast the spell'],

  noReagents: [
    'You do not have enough reagents',
    'More reagents are needed',
    'You lack the required reagents',
  ],

  noMana: ['You do not have enough mana', 'Insufficient mana'],

  alreadyUp: ['You are already under the effect'],

  disabled: ['You are no longer', 'You have dispelled'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,

  // Before throttled: waitForTextAny hands back whichever string it found, and THROTTLED_TEXT ends
  // in a bare 'You must wait' that a longer sentence can contain.
  alreadyCasting: ['You are already casting a spell', 'You are already casting'],

  throttled: THROTTLED_TEXT,
};

// trance is the only wording here that is not a guess: it is the client's own documented example.
export const MEDITATE_OUTCOME_TEXT: MeditateText = {
  trance: ['You enter a meditative trance.'],
  full: ['You are at peace'],

  // Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
  // concentration' would also match the equipped-weapon sentence.
  blocked: [
    'You cannot focus your concentration with an equipped weapon',
    'You cannot focus your concentration with an equipped shield',
    'You are preoccupied with thoughts of battle',
  ],

  unfocused: ['You cannot focus your concentration.', 'You lose your concentration'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: ['You must wait a few moments to use another skill', ...THROTTLED_TEXT],
};
