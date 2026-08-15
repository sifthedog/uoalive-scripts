// Tuned once, in src/lib/timings.ts, and re-exported here so this file stays the only one any
// consumer imports. To give training its own value for one of these, delete it from this list and
// declare it below.
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

// STALL_WARN and STALL_STOP are deliberately not in that list, and neither is createStallWatch. They
// count cycles without progress, and this script's cycles are mostly mana coming back on purpose - a
// character with a large pool and slow regeneration would trip a cycle counter while training
// perfectly well. src/selling/watch.ts skipped the stall watch for the same reason.

import type { Stage } from '../lib/stages.js';
import { SAVING_TEXT, THROTTLED_TEXT, UNSKILLED_TEXT } from '../lib/timings.js';

// --- what to train ---

export const SKILL = Skills.Bushido;

// What to call it in the log lines before the skill list has arrived, which is the only window in
// which getSkill has no name of its own
export const SKILL_LABEL = 'Bushido';

// The bands, and the whole of the policy. One row per band, in ascending order of the value it trains
// up to; the row in force is the first upTo the current value is under - see src/lib/stages.ts.
// Replacing this table is how the script trains something else.
//
// upTo is in the client's tenths: getSkill reports 74.6 as 746, so 600 is 60.0 and this run ends at
// 105.0. Exclusive, so the bands butt together with no gap and no overlap.
//
// 1050 assumes a 105 power scroll. Without one the shard caps the skill at 1000, the last band can
// never be finished, and the run sits at 100.0 until it is stopped by hand - so index.ts compares
// this against getSkill().cap at start-up and says so rather than quietly retargeting itself.
//
// mana is what the shard charges. It is the figure the mana wait gathers up to before a cast, so too
// low shows up as a noMana outcome that names itself, and too high costs a little sitting still.
//
// buff stops the run re-issuing an ability that is already standing - on a RunUO-family shard these
// are toggles, and casting again turns the move back off at the price of the cast that put it up -
// and doubles as the proof a cast landed that does not go through the journal. Drop it from a row and
// that row still trains, on the mana it spent alone.
export const STAGES: Stage[] = [
  { upTo: 600, spell: Spells.Confidence, mana: 10, buff: BuffDebuffs.Confidence },
  { upTo: 750, spell: Spells.CounterAttack, mana: 5, buff: BuffDebuffs.CounterAttack },
  { upTo: 1050, spell: Spells.Evasion, mana: 10, buff: BuffDebuffs.Evasion },
];

// --- the weapon ---

// These are weapon abilities and want something in hand, while meditation is refused while anything
// is - so the run stows the weapon for the trance and draws it again afterwards, and this is what it
// looks for when it draws. A substring, matched case-insensitively, like every other tool name here.
//
// It only has to be right for a draw that cannot use the graphic: weapon.ts learns the graphic from
// whatever is actually in hand at start-up, and the graphic is what matches from then on.
export const WEAPON_NAME = "double axe";

// The bag inside the pack to open when a plain search misses. Same escape hatch as mining's, for the
// same reason: openContainers opens the top level of the pack and no deeper.
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// How long to give a stow before reissuing it, how often to look, and how many times to try. Deliberately
// not the EQUIP_ trio, though they hold the same numbers today: an equip and a stow are independent
// facts about the shard, and sharing them would tie two unrelated knobs together and hide it.
export const DISARM_TIMEOUT = 2000;
export const DISARM_POLL = 200;
export const DISARM_ATTEMPTS = 3;

// --- reading the skill ---

// How long to wait at start-up for the client to have been sent the skill list, and how often to ask.
// Polled rather than slept through, like everything else asynchronous here: the common case is that
// it has already arrived, and then this costs one read.
export const SKILL_TIMEOUT = 1_000;
export const SKILL_POLL = 500;

// Consecutive cycles the client answered nothing for the skill before the run gives up. Counted apart
// from MAX_UNKNOWN, on mining's reasoning about noCursor: a client that has gone quiet about a skill
// is not an outcome the script failed to read, and it should not spend that budget.
export const MAX_BLIND_READS = 5;

// --- casting ---

// How long the shard may take to say something about a cast. Far shorter than the harvest scripts'
// timeouts: an ability resolves at once, with no swing animation to outlast.
export const CAST_TIMEOUT = 500;

// The pause between casts. These abilities have a cooldown of their own and the shard refuses one
// that comes too early, so this is the pacing that keeps the run out of the throttled branch rather
// than a wait for anything - the same lesson THROTTLE_BACKOFF exists for, paid up front.
export const CAST_DELAY = 500;

// Whether an ability that is already standing is left alone rather than cast again.
//
// Off, because this shard lets the same ability be recast while its buff is up - confirmed in play.
// It is a setting rather than a deletion because the other behaviour is real elsewhere: on a
// RunUO-family shard these are SpecialMoves and casting one that is already active *disables* it, so
// a run that recast blindly would gain on half its casts and pay mana to undo the other half. Turn it
// on for a shard that works that way; the symptom is the `disabled` outcome, or a buff that keeps
// going out on its own.
//
// Leaving it off costs nothing but the mana of a recast, and it is the difference between casting
// every CAST_DELAY and casting once per buff duration - which is most of the run's throughput.
export const SKIP_WHEN_BUFFED = false;

// How long to leave an ability that is already standing before looking again. Not a backoff: the buff
// expires on its own schedule and nothing the run does hurries it. Only reached when
// SKIP_WHEN_BUFFED is on, or when the shard refuses the cast in words.
export const BUFF_WAIT = 2000;

// The wait after an ability refuses on its own cooldown, growing while the refusals keep coming and
// reset by the next cast that lands. Growing rather than fixed because the cooldown is not a number
// this script knows: it varies by ability and by skill, and a backoff converges on it without having
// to be told. Evasion is the one that has a real cooldown of the three shipped stages.
//
// The ceiling is well above THROTTLE_BACKOFF_MAX on purpose. That one is sized for an action throttle
// measured in seconds; this is sized for an ability that can be a good part of a minute between uses,
// and pausing too briefly just means asking again to be told no again.
export const COOLDOWN_BACKOFF = 2000;
export const COOLDOWN_BACKOFF_MAX = 20_000;

// --- mana ---

// Whether to meditate at all. Off is a run that waits for natural regeneration, which is slower and
// always available - worth setting on a shard that refuses meditation some way this script cannot
// work around, though it works out the ordinary refusals for itself.
export const MEDITATE = true;

// Whether to fill the pool before going back to casting, or to stop as soon as the next cast is
// affordable. Full, because every stretch of meditation costs a stow and a draw - two item moves,
// each polled for proof - and that fixed cost is paid per stretch: topping the pool right off spreads
// it over many casts, where stopping at the first affordable one pays it again for every cast.
export const MEDITATE_TO_FULL = true;

// How long one trance is given to move the pool before the skill is used again, and how many times.
// A stretch is therefore bounded at four attempts of twenty seconds; a stretch that fails does not end
// the run, it costs a cycle and is counted against MAX_HUNGRY.
export const MEDITATE_TIMEOUT = 20_000;
export const MEDITATE_ATTEMPTS = 4;

// How long to give the journal, or the buff, to say the trance started
export const MEDITATE_START_TIMEOUT = 2000;

// How often the pool is read while waiting, and how often the wait says how it is coming along.
// Sliced rather than slept through, for the reason createIdleWait gives: one blocking sleep of half a
// minute leaves the client unresponsive for all of it and carries on regardless of what has happened
// to the character.
export const MANA_POLL = 500;
export const MANA_LOG_EVERY = 10_000;

// How long to wait on natural regeneration, for a run with MEDITATE off or one the shard has refused
export const REGEN_TIMEOUT = 120_000;

// Mana stretches in a row that came back empty before the run gives up. More than one, because a
// fight, a world save and a trance the shard threw away all look the same from here.
export const MAX_HUNGRY = 5;

// --- what the shard says ---

// Guesses for a RunUO-family shard, with one exception noted below. Correct them against the real
// journal after the first run - a phrase that never matches shows up as an unknown outcome, not as a
// silent wrong turn.
export const OUTCOME_TEXT = {
  // The one bucket the run does not depend on. A cast is proved by the mana leaving the pool and the
  // buff arriving, both of which are wording-free - see castOnce's silentOutcome. This is here so a
  // shard that does say something is read at once rather than waited out.
  cast: ['You have enabled', 'You are infused with', 'You gain confidence'],

  // A failed casting roll, and the commonest outcome there is at a low skill - confirmed in play,
  // where it ended a run at five in a row before it had a bucket. Ordinary rather than a fault: the
  // shard charged nothing for it, which is why it reads as silence to silentOutcome and has to be
  // read from the words instead.
  fizzled: ['The spell fizzles'],

  // Belt and braces: the loop gathers mana before it casts, so reaching this means lowerManaCost, a
  // stale read, or a mana figure in the stage row that is too low. The branch says which.
  noMana: [
    'You do not have enough mana to perform that attack',
    'You lack sufficient mana',
    'Insufficient mana',
  ],

  // Reaching this at all means the buff gate did not see the ability standing, which is worth knowing:
  // on this family of shards the next cast toggles it back off.
  alreadyUp: ['You are already under the effect'],

  disabled: ['You have disabled'],

  // These are weapon abilities on most shards, and an empty hand is what a draw that did not land
  // leaves behind - which is why the loop answers this by drawing again rather than by stopping.
  noWeapon: ['You must have a weapon', 'You cannot perform this ability'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,

  // The ability's own cooldown, and it must come before throttled: waitForTextAny hands back whichever
  // of the strings it was given it found, and THROTTLED_TEXT ends in a bare 'You must wait' that this
  // sentence contains. Listed first, it is the one that comes back - the same full-wording-before-
  // prefix ordering timings.ts uses inside THROTTLED_TEXT itself.
  //
  // Telling the two apart is not pedantry. A throttle is a fault worth giving up over after
  // MAX_THROTTLED of them; a cooldown is the ability working as designed, and Evasion spends most of
  // its time in one. Bucketed together, the Evasion stage ends every run it reaches.
  cooldown: ['You must wait before trying again'],

  throttled: THROTTLED_TEXT,
};

// The meditation wordings. trance is the one line in this file that is not a guess: it is the exact
// sentence the client's own documentation for waitForTextAny uses, in a meditation example.
//
// blocked comes before unfocused on purpose, and unfocused's general wording carries its trailing full
// stop. waitForTextAny hands back whichever of the strings it was given it found, and a stopless
// 'You cannot focus your concentration' would also match the sentence about an equipped weapon -
// leaving which of the two comes back to the client. With the stop it cannot.
export const MEDITATE_OUTCOME_TEXT = {
  trance: ['You enter a meditative trance.'],
  full: ['You are at peace'],

  // The run stows the weapon before it meditates, so reaching this means something else is refusing
  // the trance - a shield, an off-hand item, or a shard that gates meditation another way. Nothing
  // retried fixes any of those, so it latches meditation off and falls back on natural regeneration.
  blocked: [
    'You cannot focus your concentration with an equipped weapon',
    'You cannot focus your concentration with an equipped shield',
    'You are preoccupied with thoughts of battle',
  ],

  // A failed concentration roll or a trance broken by a hit. Both are fixed by using the skill again
  // in a moment, which is exactly what the bucket above is not.
  unfocused: ['You cannot focus your concentration.', 'You lose your concentration'],

  unskilled: UNSKILLED_TEXT,
  saving: SAVING_TEXT,
  throttled: ['You must wait a few moments to use another skill', ...THROTTLED_TEXT],
};
