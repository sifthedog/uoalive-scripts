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

export const SKILL = Skills.Chivalry;

// Used in the log lines until the skill list arrives
export const SKILL_LABEL = 'Chivalry';

// upTo is in the client's tenths - 450 is 45.0 - and exclusive, so the bands butt together.
//
// Every row clears its spell's own minimum by the time it is reached, which is not automatic: the
// shard requires Consecrate Weapon 15, Divine Fury 25, Enemy of One 45, Holy Light 55 and Noble
// Sacrifice 65, and a band that opened below one of them would train nothing but refusals.
//
// mana is the base cost, and a ceiling: the shard charges less as Chivalry rises. The other currency
// is not a Stage field because the run cannot gather it - every cast also spends tithing points, 10
// or 30 on the last band, and tithing is a walk and a gump away. Tithe before you paste.
export const STAGES: Stage[] = [
  // The one row that wants a weapon in hand - it enchants the weapon. index.ts stows and draws around
  // every trance when the run starts armed.
  { upTo: 450, spell: Spells.ConsecrateWeapon, mana: 10, buff: BuffDebuffs.ConsecrateWeapon },

  { upTo: 600, spell: Spells.DivineFury, mana: 15, buff: BuffDebuffs.DivineFury },
  { upTo: 700, spell: Spells.EnemyOfOne, mana: 20, buff: BuffDebuffs.EnemyOfOne },

  // No buff because the client publishes none. It damages every non-blue within a few tiles, so
  // stand somewhere empty.
  { upTo: 900, spell: Spells.HolyLight, mana: 10 },

  // No buff either, and where it finds anything to heal it sets the caster's hit points, mana and
  // stamina to 1. Alone it finds nothing and costs only the mana and the tithing.
  { upTo: 1200, spell: Spells.NobleSacrifice, mana: 20 },
];

// For the one case the graphic cannot cover: a draw attempted before anything was ever held. A
// substring, matched case-insensitively. Only the first band needs a weapon at all.
export const WEAPON_NAME = 'sword';

// The bag inside the pack to open when a plain search misses
export const SPARE_BAG_SERIAL: number | undefined = undefined;

export const DISARM_TIMEOUT = 2000;
export const DISARM_POLL = 200;
export const DISARM_ATTEMPTS = 3;

// The fraction of maximum health below which the run bandages itself, and stops if that cannot get
// it back above the line. Noble Sacrifice is why: cast where there is anything to heal it drops the
// caster to 1 hit point, and a pet or a passing blue inside 6 tiles is enough.
export const HURT_FLOOR = 0.5;

// Off is a run that simply stops when it is hurt.
export const BANDAGE = true;

// Clean bandages only: the bloodied ones are a different item and cannot be applied.
export const BANDAGE_GRAPHIC = 0x0e21;

export const BANDAGE_ATTEMPTS = 4;

// Bandaging is seconds rather than milliseconds
export const BANDAGE_TIMEOUT = 8000;

// A heal is proved by the hits going up, so these only explain the failures.
export const HEAL_OUTCOME_TEXT: HealText = {
  healed: ['You finish applying the bandages', 'You heal', 'You apply the bandages'],

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

// Pacing rather than a wait. None of these spells has a long incantation, so this is the weapon
// trainer's figure; the alreadyCasting backoff catches whatever it misses.
export const CAST_DELAY = 500;

// Gating on the buff would cap the run at one cast per buff duration.
export const SKIP_WHEN_BUFFED = false;

// On, because Enemy of One toggles: cast while it is standing it comes off, and the shard charges the
// mana and the tithing and rolls the skill for that exactly as it does for putting it up.
export const DISABLED_IS_PROGRESS = true;

export const BUFF_WAIT = 2000;

// Nothing to out-wait but the spell's own casting time
export const CASTING_WAIT = 750;

// None of these spells has a cooldown, so what this actually backs off from is alreadyCasting.
export const COOLDOWN_BACKOFF = 1000;
export const COOLDOWN_BACKOFF_MAX = 8000;

// Off is a run that waits for natural regeneration.
export const MEDITATE = true;

// Where the run is armed, every stretch of meditation costs a stow and a draw, and that fixed cost is
// paid per stretch rather than per cast.
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


// Guesses - correct them against the real journal after the first run. A phrase that never matches
// shows up as an unknown outcome, not as a silent wrong turn.
export const OUTCOME_TEXT: OutcomeText = {
  // Not depended on: the mana leaving the pool and the buff arriving are the proof
  cast: ['You are now', 'Your weapon is consecrated', 'You are filled with divine fury'],

  fizzled: ['You fail to cast the spell', 'The spell fizzles'],

  // The one this script is likeliest to end on. Nothing to do about it but go and tithe more gold.
  noTithing: [
    'You do not have enough tithing points',
    'You must have at least',
    'You need to make an offering',
  ],

  noMana: ['You do not have enough mana', 'Insufficient mana'],

  alreadyUp: ['You are already under the effect'],

  // Enemy of One coming off. DISABLED_IS_PROGRESS is what tells the loop to count it rather than
  // complain about it.
  disabled: ['You are no longer', 'You lose your focus'],

  // Karma lives in this bucket rather than one of its own: Enemy of One and Noble Sacrifice want it
  // positive, and a character without it cannot cast them at all - which is what unskilled means and
  // what stopping is the right answer to.
  unskilled: [
    'You are not pious enough',
    'Your karma is not high enough',
    'You must have proper karma',
    ...UNSKILLED_TEXT,
  ],

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
  //
  // The run stows the weapon before meditating, so reaching this means something else is refusing the
  // trance: a shield, an off-hand item, or a shard that gates meditation another way.
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
