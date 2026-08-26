// Re-exported rather than imported directly so this file stays the only one consumers import.
export {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  HEARTBEAT_EVERY,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_THROTTLED,
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
// castTimeout and castDelay are per row because the circles are seconds apart in cast time, and one
// figure for the table means the 3rd circle waits out the 8th's incantation on every cast. The
// timeouts are the circle's usual cast time with a margin on top - a shard with faster casting can
// have them all down, and one without has to have the 8th circle's up rather than read every
// Earthquake as unreadable. See CAST_TIMEOUT for why the margin is not free.
export const STAGES: Stage[] = [
  // 3rd circle. Below about 30 the sensible thing is to buy the skill from an NPC trainer.
  {
    upTo: 450,
    spell: Spells.Bless,
    mana: 9,
    buff: BuffDebuffs.Bless,
    target: 'self',
    castTimeout: 1200,
    castDelay: 300,
  },

  // 4th circle
  {
    upTo: 600,
    spell: Spells.ArchProtection,
    mana: 11,
    buff: BuffDebuffs.ArchProtection,
    target: 'self',
    castTimeout: 1500,
    castDelay: 350,
  },

  // 6th. The 5th and 7th circles are skipped because their spells want a cursor over ground or a
  // gump answered, and neither is something this loop can do.
  {
    upTo: 800,
    spell: Spells.Invisibility,
    mana: 20,
    buff: BuffDebuffs.Invisibility,
    target: 'self',
    castTimeout: 2500,
    castDelay: 400,
  },

  // 8th. An area attack that hits everything nearby, so this band belongs somewhere empty. The
  // longest timeout of the four and the only row that needs it: no buff, so the mana falling is the
  // whole proof, and a window that closes first turns every cast here into an unread outcome.
  { upTo: 1200, spell: Spells.Earthquake, mana: 50, castTimeout: 3200, castDelay: 600 },
];

export const SKILL_TIMEOUT = 1_000;
export const SKILL_POLL = 500;

// Consecutive cycles the client answered nothing for the skill before giving up
export const MAX_BLIND_READS = 5;

// Both of these are now only the fallback for a row that names neither, and every row in STAGES
// names both - they are kept because the shared loop and caster take them, and because a row added
// without a figure of its own should land on something sane rather than on nothing.
//
// A spell has an incantation to get through, and a refusal arriving after the wait has closed reads
// as an unknown outcome. Longer than the other folders' 500 for a second reason: a cast the shard
// says nothing about is proved by the mana leaving the pool, and it does not leave until the
// incantation finishes, so a window shorter than the cast makes every success unreadable. The margin
// over the cast time is not free either - a successful cast says nothing, so it spends the whole
// window every time.
export const CAST_TIMEOUT = 2000;

// Pacing on top of that window, not a wait for the incantation - castOnce has already stood through
// it by the time the loop sleeps here, so what this used to buy at 3000 was idle. Overshooting a
// slow row costs one alreadyCasting and its flat CASTING_WAIT, which is the cheaper mistake.
export const CAST_DELAY = 750;

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

// Casting cycles that produced neither a readable cast nor any movement in the skill before the run
// gives up - the only thing left that ends a run for getting nowhere. Generous on purpose: an outcome
// this loop cannot read is a log problem, not a reason to stop, and the skill moving clears it. A dry
// mana stretch is charged what it cost in cycles, so this ceiling covers that case too.
//
// Raised from 200 with the weighting it is read against: a stretch is charged regenTimeout over the
// cost of one casting cycle, which on the Bless row is 120000/1500 = 80. At 200 that was two failed
// trances and the run was over, and a full pool inside four attempts is not something a character
// with low Meditation manages every time. 500 puts the Bless row back at six and leaves the
// Earthquake row - the slowest cycle and so the cheapest per stretch - at fifteen.
export const MAX_STALE = 500;

// In the order it comes off, which is also the order it goes back on. Hands first: they are the only
// layers whose absence ends a run. Necklace is here for gorgets; the rest has blocked no trance yet.
export const STRIP_LAYERS: Layer[] = [
  Layers.OneHanded,
  Layers.TwoHanded,
  Layers.Helmet,
  Layers.Necklace,
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

// On. The escalation this used to default to only fires when the shard answers one of the wordings in
// MEDITATE_OUTCOME_TEXT.blocked, and those are RunUO-family guesses - a shard that refuses the trance
// in words this table has not got, or that quietly slows the regeneration instead of refusing
// anything, leaves the armour on for ever and the run never finds out. Stripping up front does not
// depend on reading the shard's mind. Set it back to false to save the item moves on a shard where
// the hands alone turn out to be enough.
export const STRIP_AT_ONCE = true;

// Deliberately not the EQUIP_ trio, though they hold the same numbers today: an equip and a stow are
// independent facts about the shard.
export const DISARM_TIMEOUT = 2000;
export const DISARM_POLL = 200;
export const DISARM_ATTEMPTS = 3;


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
