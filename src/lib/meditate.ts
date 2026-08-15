// Waiting for mana to come back - meditating where the shard allows it, and simply standing there
// where it does not.
//
// A factory rather than a module: it holds two latches, and two scripts in one test process must not
// share them.

import { outcomeVocabulary } from './outcomes.js';
import { manaCeiling } from './vitals.js';

export type MeditateOutcomeName =
  | 'trance'
  | 'full'

  // Refused for something the run cannot take off, so nothing retried fixes it
  | 'blocked'

  // A failed concentration roll or a trance broken by a hit, which using the skill again does fix
  | 'unfocused'
  | 'unskilled'
  | 'saving'
  | 'throttled';

export type MeditateText = Partial<Record<MeditateOutcomeName, string[]>>;

export type MeditateOutcome = MeditateOutcomeName | 'unknown';

export interface ManaWaitOptions {
  prefix: string;

  outcomeText: MeditateText;

  meditate: boolean;

  // Whether to fill the pool before going back to casting, or to stop as soon as the next cast is
  // affordable
  toFull: boolean;

  timeoutMs: number;
  attempts: number;

  startTimeoutMs: number;

  pollMs: number;
  logEveryMs: number;

  regenTimeoutMs: number;

  // Both or neither: a run that can stow but not restore leaves a character holding nothing, which
  // is the state this module is most careful to avoid.
  stow?: () => boolean;
  restore?: () => boolean;

  // Asked for only when a trance was refused with the hands already empty, so what the shard objects
  // to is worn rather than held. Answering false is what tells this module the escalation is spent -
  // without it a refusal is a dead end, and meditation is written off for the whole run.
  stripMore?: () => boolean;

  stopReason: () => string | undefined;
  resetBeat: () => void;
  waitOutSave: () => void;
}

export interface ManaWait {
  regainMana: (need: number) => boolean;

  manaTarget: (need: number) => number;

  // Set when what was stowed could not be put back. Reported through the loop's tail rather than
  // thrown from here, so every ending is said in one place.
  blocked: () => string | undefined;
}

export const createManaWait = ({
  prefix,
  outcomeText,
  meditate,
  toFull,
  timeoutMs,
  attempts,
  startTimeoutMs,
  pollMs,
  logEveryMs,
  regenTimeoutMs,
  stow,
  restore,
  stripMore,
  stopReason,
  resetBeat,
  waitOutSave,
}: ManaWaitOptions): ManaWait => {
  const { all, outcomeFor } = outcomeVocabulary(outcomeText);

  // Latched on the wording only and never on silence: a world save is silent in exactly the way a
  // refusal is, and reading one as the other would give up meditation for a whole run over a pause.
  let refused: string | undefined;

  let unrestored: string | undefined;

  // Worked out on every read rather than once: maxMana is 0 while the client refreshes stats, and a
  // ceiling taken in that window would either end the wait as it started or never end it at all.
  const manaTarget = (need: number): number => {
    const ceiling = manaCeiling();

    if (!toFull || ceiling === undefined) {
      return need;
    }

    return Math.max(need, ceiling);
  };

  // >= and never !=. The script this replaces waited on `mana != maxMana`, which is two faults in one
  // comparison: a regenerating pool passes a figure as often as it lands on it, and a maximum that
  // moves - a stat refresh, a buff, a ring taken off - is never equal to anything for long.
  const enough = (need: number): boolean => player.mana >= manaTarget(need);

  const meditating = (): boolean => player.hasBuffDebuff(BuffDebuffs.ActiveMeditation);

  // Sliced rather than slept through: one blocking sleep of half a minute leaves the client
  // unresponsive for all of it and carries on regardless of what has happened to the character.
  const watchMana = (need: number, waitMs: number): boolean => {
    let since = 0;

    for (let waited = 0; waited < waitMs; waited += pollMs) {
      if (enough(need)) {
        return true;
      }

      if (stopReason()) {
        return false;
      }

      sleep(pollMs);
      since += pollMs;

      if (since >= logEveryMs) {
        since = 0;
        log(
          `${prefix}: ${player.mana}/${manaTarget(need)} mana${meditating() ? ', meditating' : ''}`,
        );
      }
    }

    return enough(need);
  };

  // The journal first, because it is the only thing that says why, and it has been clear since
  // immediately before the use.
  const startOutcome = (): MeditateOutcome => {
    const matched = journal.waitForTextAny(all, undefined, startTimeoutMs);

    if (matched) {
      return outcomeFor(matched) ?? 'unknown';
    }

    // Silence is what every use looks like on a shard whose wordings this table has wrong,
    // so the buff is the proof that does not go through the journal at all. waitForBuffDebuff
    // answers null when it has nothing to say, which is neither a yes nor a no.
    return player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, startTimeoutMs) === true
      ? 'trance'
      : 'unknown';
  };

  // Not untilLanded, which fits a silent all-or-nothing equip of a couple of seconds. This wait runs
  // for the best part of a minute, hundreds of times a run, and needs three things that one does not
  // do: the guards get a look in, it says how the pool is coming along, and it does not reissue into
  // a trance that is demonstrably still running.
  //
  // No early return may skip past this function's caller, which is what puts the hands back.
  const meditateFor = (need: number): boolean => {
    for (let attempt = 1; attempt <= attempts; attempt++) {
      // Using the skill again mid-trance is at best a wasted action and at worst the shard ending the
      // very trance this attempt is waiting on. A shard that publishes no buff answers false here.
      if (!meditating()) {
        journal.clear();
        player.useSkill(Skills.Meditation);

        const outcome = startOutcome();

        // The hands are already empty here, so what the shard objects to is worn. Costs one attempt
        // and can only ever cost one: stripMore answers false from its second call onwards.
        if (outcome === 'blocked' && stripMore?.()) {
          log(`${prefix}: the trance was refused with armour on - took more off, trying again`);

          // Not a fall-through to the watchMana below: the trance never started, so there is no pool
          // to watch for a whole timeoutMs and nothing to say about it.
          continue;
        }

        // Whatever the caller could take off is now off, so what refuses the trance is out of reach.
        // No amount of undressing raises a skill, which is why unskilled never asks for the strip.
        if (outcome === 'blocked' || outcome === 'unskilled') {
          refused = `the shard refuses meditation (${outcome})`;
          log(`${prefix}: ${refused} - check the off-hand; falling back on natural regeneration`);

          return watchMana(need, regenTimeoutMs);
        }

        // The shard saying the pool is already full, which it can know better than a stat read does
        if (outcome === 'full') {
          return true;
        }

        // A pause and not a refusal: nothing about meditation is learned from it
        if (outcome === 'saving') {
          waitOutSave();
        }
      }

      if (watchMana(need, timeoutMs)) {
        return true;
      }

      // Not "gave up": a failed concentration roll, a trance broken by a hit and a use the shard
      // threw away all look like this, and all are answered by using the skill again.
      log(`${prefix}: meditation attempt ${attempt} did not fill the pool, using the skill again`);
    }

    return false;
  };

  return {
    manaTarget,
    blocked: () => unrestored,

    // Returns whether the mana actually arrived; what a failure means is the loop's to say.
    regainMana: (need) => {
      if (enough(need)) {
        return true;
      }

      log(`${prefix}: ${player.mana} mana, waiting for ${manaTarget(need)}`);

      // Whether this wait undresses at all, kept apart from whether the undressing worked: a stow
      // that will not land just means waiting on natural regeneration with the weapon still held.
      const clearing = meditate && !refused;
      const clear = clearing && (stow?.() ?? true);
      const arrived = clear ? meditateFor(need) : watchMana(need, regenTimeoutMs);

      // Gated on `clearing` and not on `clear`: a stow that moves four pieces and fails on the fifth
      // answers false, and gating the restore on that would leave those four in the pack for the rest
      // of the run.
      //
      // Otherwise unconditional, and the single exit path every outcome flows through. A character
      // left holding nothing casts into a permanent noWeapon refusal and cannot defend itself.
      if (clearing && restore && !restore()) {
        unrestored = 'could not get the weapon back in hand';
      }

      // This path has just spent up to a minute reporting on its own cadence, so the next beat starts
      // a full interval from here rather than landing on top of the line above
      resetBeat();

      return arrived;
    },
  };
};
