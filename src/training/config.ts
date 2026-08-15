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
} from "../lib/timings.js";

// STALL_WARN and STALL_STOP are left out: a cycle counter reads a character meditating on purpose
// as a run that has stopped getting anywhere.

import type { OutcomeText } from "../lib/cast.js";
import type { Layer } from "../lib/gear.js";
import type { MeditateText } from "../lib/meditate.js";
import type { Stage } from "../lib/stages.js";
import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from "../lib/timings.js";

export const SKILL = Skills.Bushido;

// Used in the log lines until the skill list arrives
export const SKILL_LABEL = "Bushido";

// upTo is in the client's tenths - 600 is 60.0 - and exclusive, so the bands butt together.
//
// 1050 assumes a 105 power scroll; without one the shard caps the skill at 1000 and the last band
// can never be finished, which the loop says at start-up rather than quietly retargeting itself.
//
// buff stops the run re-issuing an ability that is already standing, and doubles as the proof a cast
// landed that does not go through the journal.
export const STAGES: Stage[] = [
  {
    upTo: 600,
    spell: Spells.Confidence,
    mana: 10,
    buff: BuffDebuffs.Confidence,
  },
  {
    upTo: 750,
    spell: Spells.CounterAttack,
    mana: 5,
    buff: BuffDebuffs.CounterAttack,
  },
  {
    upTo: 1050,
    spell: Spells.MomentumStrike,
    mana: 10,
    buff: BuffDebuffs.MomentumStrike,
  },
];

// Matched as a substring, case-insensitively. Only used for a draw that cannot use the graphic:
// weapon.ts learns the graphic from whatever is in hand at start-up.
export const WEAPON_NAME = "double axe";

// The bag inside the pack to open when a plain search misses - openContainers opens the top level of
// the pack and no deeper.
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// Deliberately not the EQUIP_ trio, though they hold the same numbers today: an equip and a stow are
// independent facts about the shard.
export const DISARM_TIMEOUT = 2000;
export const DISARM_POLL = 200;
export const DISARM_ATTEMPTS = 3;

export const SKILL_TIMEOUT = 1_000;
export const SKILL_POLL = 500;

// Consecutive cycles the client answered nothing for the skill before giving up
export const MAX_BLIND_READS = 5;

// Far shorter than the harvest scripts' timeouts: an ability resolves at once, with no swing
// animation to outlast.
export const CAST_TIMEOUT = 500;

// Pacing rather than a wait: these abilities have cooldowns of their own and the shard refuses one
// that comes too early.
export const CAST_DELAY = 500;

// Off, because this shard lets the same ability be recast while its buff is up - confirmed in play.
// Turn it on for a RunUO-family shard where these are SpecialMoves and a second cast *disables* the
// one already standing; the symptom is the `disabled` outcome, or a buff that keeps going out.
export const SKIP_WHEN_BUFFED = false;

// Not a backoff: the buff expires on its own schedule and nothing the run does hurries it.
export const BUFF_WAIT = 2000;

// Nothing to out-wait but the ability's own casting time
export const CASTING_WAIT = 750;

// Growing rather than fixed because the cooldown is not a number this script knows - it varies by
// ability and by skill. The ceiling is well above THROTTLE_BACKOFF_MAX because an ability can be a
// good part of a minute between uses.
export const COOLDOWN_BACKOFF = 2000;
export const COOLDOWN_BACKOFF_MAX = 20_000;

// Off waits for natural regeneration instead: slower, always available.
export const MEDITATE = true;

// Every stretch of meditation costs a stow and a draw, so topping the pool right off spreads that
// fixed cost over many casts.
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

// More than one, because a fight, a world save and a discarded trance all look the same from here.

// Guesses - correct them against the real journal after the first run. A phrase that never matches
// shows up as an unknown outcome, not as a silent wrong turn.
export const OUTCOME_TEXT: OutcomeText = {
  // Not depended on: the mana leaving the pool and the buff arriving are the proof
  cast: ["You have enabled", "You are infused with", "You gain confidence"],

  // The commonest outcome at a low skill. The shard charges nothing for it, which is why it reads as
  // silence to silentOutcome and has to be read from the words instead.
  fizzled: ["The spell fizzles"],

  noMana: [
    "You do not have enough mana to perform that attack",
    "You lack sufficient mana",
    "Insufficient mana",
  ],

  alreadyUp: ["You are already under the effect"],

  disabled: ["You have disabled"],

  // An empty hand is what a draw that did not land leaves behind, which is why the loop answers this
  // by drawing again rather than by stopping.
  noWeapon: ["You must have a weapon", "You cannot perform this ability"],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,

  // Must come before throttled: waitForTextAny hands back whichever string it found, and
  // THROTTLED_TEXT ends in a bare 'You must wait' that this sentence contains. Bucketed together,
  // Evasion's ordinary cooldown would end every run that reaches its band.
  cooldown: ["You must wait before trying again"],

  throttled: THROTTLED_TEXT,
};

// trance is the only wording here that is not a guess: it is the client's own documented example.
export const MEDITATE_OUTCOME_TEXT: MeditateText = {
  trance: ["You enter a meditative trance."],
  full: ["You are at peace"],

  // Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
  // concentration' would also match the equipped-weapon sentence.
  //
  // The run stows the weapon before meditating, so reaching this means something else is refusing
  // the trance and nothing retried fixes it: meditation latches off and regeneration takes over.
  blocked: [
    "You cannot focus your concentration with an equipped weapon",
    "You cannot focus your concentration with an equipped shield",
    "You are preoccupied with thoughts of battle",
  ],

  // A failed roll or a trance broken by a hit - both fixed by using the skill again in a moment
  unfocused: [
    "You cannot focus your concentration.",
    "You lose your concentration",
  ],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: [
    "You must wait a few moments to use another skill",
    ...THROTTLED_TEXT,
  ],
};
