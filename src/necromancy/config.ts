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
  TARGET_TIMEOUT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from '../lib/timings.js';

// STALL_WARN and STALL_STOP are left out: a cycle counter reads a character meditating on purpose
// as a run that has stopped getting anywhere.

import type { OutcomeText } from '../lib/cast.js';
import type { HealText } from '../lib/heal.js';
import type { Layer } from '../lib/gear.js';
import type { MeditateText } from '../lib/meditate.js';
import type { Stage } from '../lib/stages.js';
import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

export const SKILL = Skills.Necromancy;

// Used in the log lines until the skill list arrives
export const SKILL_LABEL = 'Necromancy';

// upTo is in the client's tenths - 500 is 50.0 - and exclusive, so the bands butt together.
//
// 1200 assumes the power scrolls; without them the shard caps the skill at 1000 and the last two
// bands can never be finished, which the loop says at start-up rather than quietly retargeting.
//
// Every row is castable by the time it is reached, which is not automatic: the shard has its own
// minimum per spell (Pain Spike 20, Horrific Beast 40, Wither 60, Lich Form 70, Vampiric Embrace 99)
// and a band that opened below one of them would train nothing but the unskilled outcome.
export const STAGES: Stage[] = [
  // Cast at the character rather than at a creature, which would be a punchbag to find, keep alive
  // and keep in range. It costs health instead, which is what HURT_FLOOR is for.
  { upTo: 500, spell: Spells.PainSpike, mana: 5, buff: BuffDebuffs.PainSpike, target: 'self' },

  { upTo: 700, spell: Spells.HorrificBeast, mana: 11, buff: BuffDebuffs.HorrificBeast },

  // No buff because the client publishes none for it - the mana leaving the pool is the proof. It is
  // also the one band that hits everything standing nearby.
  { upTo: 900, spell: Spells.Wither, mana: 23 },

  { upTo: 1000, spell: Spells.LichForm, mana: 23, buff: BuffDebuffs.LichForm },
  { upTo: 1200, spell: Spells.VampiricEmbrace, mana: 23, buff: BuffDebuffs.VampiricEmbrace },
];

// The fraction of maximum health below which the run bandages itself, and stops if that cannot get
// it back above the line. This script hurts its own character twice over - Pain Spike is cast at it
// and Lich Form drains it for a whole band - so `dead` alone is a brake that works too late.
export const HURT_FLOOR = 0.5;

// Off is a run that simply stops when it is hurt, for a character with something better to heal with.
export const BANDAGE = true;

// Clean bandages only: the bloodied ones are a different item and cannot be applied.
export const BANDAGE_GRAPHIC = 0x0e21;

// More than one because a bandage can be interrupted, and one heals a fraction of the pool at the
// skill a necromancer usually has.
export const BANDAGE_ATTEMPTS = 4;

// Bandaging is seconds rather than milliseconds, and the wait covers the whole application.
export const BANDAGE_TIMEOUT = 8000;

// Nothing load-bearing rests on these: a heal is proved by the hits going up.
export const HEAL_OUTCOME_TEXT: HealText = {
  healed: ['You finish applying the bandages', 'You heal', 'You apply the bandages'],

  // The pack search notices this first on most shards, so reaching it means bandages that vanished
  // between the search and the use.
  noBandages: [
    'You do not have a bandage',
    'You must have bandages',
    'You do not have any bandages',
  ],

  busy: ['You are already applying bandages'],
  interrupted: ['You have been interrupted'],
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};

export const SKILL_TIMEOUT = 1_000;
export const SKILL_POLL = 500;

// Consecutive cycles the client answered nothing for the skill before giving up
export const MAX_BLIND_READS = 5;

export const CAST_TIMEOUT = 500;

// Pacing rather than a wait: these spells have no cooldown, but the shard's action throttle is real
// and a loop with no pause re-arms it with every retry.
export const CAST_DELAY = 500;

// Off, and not as a preference: three of these five bands are transformations, which stand until
// re-cast. Gated on the buff, the run would cast Horrific Beast once and wait forever for a form
// that is not going anywhere.
export const SKIP_WHEN_BUFFED = false;

// On, because re-casting is how the character leaves a form: it costs mana and rolls the skill
// exactly like the cast that put it up. Turn it off for a table of spells that stack.
export const DISABLED_IS_PROGRESS = true;

export const BUFF_WAIT = 2000;

// Sized to out-wait the cast itself and nothing more. Raise it if the journal fills with 'You are
// already casting a spell'; lower it if the run sits idle between casts.
export const CASTING_WAIT = 750;

// Unreachable here - with no cooldown phrase in OUTCOME_TEXT the branch that uses these cannot be
// taken - but the loop takes them.
export const COOLDOWN_BACKOFF = 2000;
export const COOLDOWN_BACKOFF_MAX = 20_000;

// Off waits for natural regeneration instead: slower, always available.
export const MEDITATE = true;

// Four of the five bands charge 23 mana against a pool that is rarely more than a few casts deep, so
// stopping at the first affordable cast means meditating again immediately after it.
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
export const MAX_STALE = 200;

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

// More than one, because a fight, a world save and a discarded trance all look the same from here.

// Guesses - correct them against the real journal after the first run. A phrase that never matches
// shows up as an unknown outcome, not as a silent wrong turn.
export const OUTCOME_TEXT: OutcomeText = {
  // Not depended on: the mana leaving the pool and the buff arriving are the proof
  cast: ['You are surrounded by a red aura', 'You feel a sudden surge of power'],

  // The commonest outcome at a low skill. The shard charges nothing for it, which is why it reads as
  // silence to silentOutcome and has to be read from the words instead.
  fizzled: ['The spell fizzles', 'You have failed to cast the spell'],

  noMana: ['You do not have enough mana', 'Insufficient mana'],

  // The one refusal here that nothing waited for fixes
  noReagents: [
    'You do not have enough reagents',
    'More reagents are needed',
    'You lack the required reagents',
  ],

  alreadyUp: ['You are already under the effect'],

  // The transformation coming off, which is how the character leaves a form and half of what a form
  // band does. DISABLED_IS_PROGRESS is what tells the loop to count it rather than complain.
  disabled: ['You are no longer', 'You return to your normal form', 'You have disabled'],

  alreadyCasting: ['You are already casting a spell', 'You are already casting'],

  // Horrific Beast is the one that does this on an OSI-faithful shard, and if the form spell itself
  // is refused then that band cannot train at all - worth being told once.
  formLocked: [
    'You cannot cast that spell in this form',
    'You can not cast this spell while polymorphed',
    'You cannot use that ability in this form',
  ],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: THROTTLED_TEXT,
};

// trance is the only wording here that is not a guess: it is the client's own documented example.
export const MEDITATE_OUTCOME_TEXT: MeditateText = {
  trance: ['You enter a meditative trance.'],
  full: ['You are at peace'],

  // Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
  // concentration' would also match the equipped-weapon sentence.
  //
  // This run stows nothing, so reaching this latches meditation off for the rest of the run and
  // falls back on natural regeneration. Start with empty hands.
  blocked: [
    'You cannot focus your concentration with an equipped weapon',
    'You cannot focus your concentration with an equipped shield',
    'You are preoccupied with thoughts of battle',
  ],

  // A failed roll or a trance broken by a hit - both fixed by using the skill again in a moment
  unfocused: ['You cannot focus your concentration.', 'You lose your concentration'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: ['You must wait a few moments to use another skill', ...THROTTLED_TEXT],
};
