import { outcomeVocabulary } from '../lib/outcomes.js';
import { manaCeiling } from '../lib/vitals.js';
import {
  MANA_LOG_EVERY,
  MANA_POLL,
  MEDITATE,
  MEDITATE_ATTEMPTS,
  MEDITATE_OUTCOME_TEXT,
  MEDITATE_START_TIMEOUT,
  MEDITATE_TIMEOUT,
  MEDITATE_TO_FULL,
  REGEN_TIMEOUT,
} from './config.js';
import { stopReason } from './guards.js';
import { resetBeat } from './heartbeat.js';
import { waitOutSave } from './save.js';
import { disarm, rearm } from './weapon.js';

export type MeditateOutcome = keyof typeof MEDITATE_OUTCOME_TEXT | 'unknown';

export const { all: ALL_MEDITATE_TEXT, outcomeFor: meditateOutcomeFor } =
  outcomeVocabulary(MEDITATE_OUTCOME_TEXT);

// Latched off the first time the shard says outright that it will not have it. Latched on the wording
// only and never on silence: a world save is silent in exactly the way a refusal is, and reading one
// as the other would give up meditation for the rest of a run over a pause.
let refused: string | undefined;

// Set when the weapon could not be got back into the character's hand, which is the one thing this
// module can discover that has to end the run. Reported through the loop's tail rather than thrown
// from here, so every ending is said in one place.
let disarmed: string | undefined;

export const weaponLost = (): string | undefined => disarmed;

// How much to gather before going back to casting. Worked out on every read rather than once: maxMana
// is 0 while the client refreshes stats, and a ceiling taken once in that window would either end the
// wait the instant it started or never end it at all.
export const manaTarget = (need: number): number => {
  const ceiling = manaCeiling();

  if (!MEDITATE_TO_FULL || ceiling === undefined) {
    return need;
  }

  return Math.max(need, ceiling);
};

// >= and never !=. The script this replaces waited on `mana != maxMana`, which is two faults in one
// comparison: a regenerating pool passes a figure as often as it lands on it, and a maximum that
// moves - a stat refresh, a buff, a ring taken off - is never equal to anything for long.
const enough = (need: number): boolean => player.mana >= manaTarget(need);

const meditating = (): boolean => player.hasBuffDebuff(BuffDebuffs.ActiveMeditation);

// Sliced rather than slept through, on createIdleWait's reasoning: one blocking sleep of half a minute
// leaves the client unresponsive for all of it and carries on regardless of what has happened to the
// character. The guards get a look in every poll, and the pool is reported on the way up.
const watchMana = (need: number, timeoutMs: number): boolean => {
  let since = 0;

  for (let waited = 0; waited < timeoutMs; waited += MANA_POLL) {
    if (enough(need)) {
      return true;
    }

    if (stopReason()) {
      return false;
    }

    sleep(MANA_POLL);
    since += MANA_POLL;

    if (since >= MANA_LOG_EVERY) {
      since = 0;
      log(`train: ${player.mana}/${manaTarget(need)} mana${meditating() ? ', meditating' : ''}`);
    }
  }

  return enough(need);
};

// What the shard made of the use. The journal first, because it is the only thing that says why - the
// buff below says only that it worked - and it has been clear since immediately before the use, so
// whatever is in it now arrived because of it.
const startOutcome = (): MeditateOutcome => {
  const matched = journal.waitForTextAny(ALL_MEDITATE_TEXT, undefined, MEDITATE_START_TIMEOUT);

  if (matched) {
    return meditateOutcomeFor(matched) ?? 'unknown';
  }

  // Silent, which is what every use looks like on a shard whose wordings this table has wrong. The
  // buff is the proof that does not go through the journal at all. waitForBuffDebuff answers null
  // when it has nothing to say, which is neither a yes nor a no and is read as the silence it is.
  return player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, MEDITATE_START_TIMEOUT) === true
    ? 'trance'
    : 'unknown';
};

// untilLanded is the right shape for this - issue, poll for the proof, reissue - but not the right
// helper: that one fits a silent all-or-nothing equip of a couple of seconds, and this wait runs for
// the best part of a minute, hundreds of times a run. It needs three things untilLanded does not do:
// the guards get a look in while it waits, it says how the pool is coming along rather than going
// quiet, and it does not reissue into a trance that is demonstrably still running.
//
// No early return may skip past this function's caller, which is what puts the weapon back.
const meditateFor = (need: number): boolean => {
  for (let attempt = 1; attempt <= MEDITATE_ATTEMPTS; attempt++) {
    // Not re-issued into a trance that is already running: using the skill again is at best a wasted
    // action and at worst the shard ending the very trance this attempt is waiting on. A shard that
    // publishes no buff answers false here, which is the old behaviour of using it every attempt.
    if (!meditating()) {
      journal.clear();
      player.useSkill(Skills.Meditation);

      const outcome = startOutcome();

      // Nothing retried fixes either of these. The weapon is already stowed by the time this runs, so
      // whatever is refusing the trance is something else the run cannot take off - a shield, an
      // off-hand item, or a shard that gates meditation another way.
      if (outcome === 'blocked' || outcome === 'unskilled') {
        refused = `the shard refuses meditation (${outcome})`;
        log(`train: ${refused} - check the off-hand; falling back on natural regeneration`);

        return watchMana(need, REGEN_TIMEOUT);
      }

      // The shard saying the pool is already full, which it can know better than a stat read does
      if (outcome === 'full') {
        return true;
      }

      // A pause and not a refusal: nothing about meditation is learned from it, so it costs the wait
      // and nothing else
      if (outcome === 'saving') {
        waitOutSave();
      }
    }

    if (watchMana(need, MEDITATE_TIMEOUT)) {
      return true;
    }

    // Not "gave up": a failed concentration roll, a trance broken by a hit, and a use the shard threw
    // away all look like this, and all of them are answered by using the skill again.
    log(`train: meditation attempt ${attempt} did not fill the pool, using the skill again`);
  }

  return false;
};

// Wait for mana to come back - meditating where the shard allows it, and simply standing there where
// it does not. Returns whether the mana actually arrived; what a failure means is the loop's to say.
export const regainMana = (need: number): boolean => {
  if (enough(need)) {
    return true;
  }

  log(`train: ${player.mana} mana, waiting for ${manaTarget(need)}`);

  // Meditating with a weapon in hand is refused outright, so the stow is what makes the trance
  // possible at all. A stow that will not land is not a reason to give up: it is a run that waits on
  // natural regeneration with the weapon still held, which is slower and always available.
  const stowed = MEDITATE && !refused && disarm();
  const arrived = stowed ? meditateFor(need) : watchMana(need, REGEN_TIMEOUT);

  // Unconditional, and the single exit path every outcome above flows through - success, a timeout, a
  // latched refusal and a guard firing mid-trance all reach it. A character left holding nothing casts
  // into a permanent noWeapon refusal and cannot defend itself, which is strictly worse than never
  // having meditated at all.
  if (stowed && !rearm()) {
    disarmed = 'could not get the weapon back in hand';
  }

  // This path reports on its own cadence and has just spent up to a minute doing it, so the next beat
  // starts a full interval from here rather than landing on top of the line above
  resetBeat();

  return arrived;
};
