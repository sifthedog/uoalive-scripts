// Bandaging the character it is run on, for a script whose own work costs health. The idiom is the
// client's own, from the documentation for target.waitTargetSelf.
//
// A factory, because it latches an empty pack for the rest of the run.

import { outcomeVocabulary } from './outcomes.js';

export type HealOutcomeName =
  // The shard saying the bandage did its work. Never relied on - the hits are the proof.
  | 'healed'

  // The one failure nothing retried fixes
  | 'noBandages'

  // A bandage already going on. Waiting is the whole answer to it.
  | 'busy'

  // A bandage that came off early: hit, moved, or the shard threw the action away
  | 'interrupted'
  | 'saving'
  | 'throttled';

export type HealText = Partial<Record<HealOutcomeName, string[]>>;

export interface BandagerOptions {
  prefix: string;

  // 0xE21 is a clean bandage on every shard this repo has seen; a bloodied one is a different item
  // and cannot be applied.
  graphic: number;

  outcomeText: HealText;

  timeoutMs: number;
  cursorTimeoutMs: number;
  attempts: number;

  // Asked rather than measured here, so the floor that triggers the healing and the floor that stops
  // the run are the same number written once.
  recovered: () => boolean;

  waitOutSave: () => void;
}

export interface Bandager {
  // Answers whether the character got back above the floor; what a failure means is the caller's to
  // say - and for both trainers it means the guard that asked for the healing now ends the run.
  mend: () => boolean;

  // Set once the pack has no bandages left. Said once rather than every cycle.
  empty: () => string | undefined;
}

export const createBandager = ({
  prefix,
  graphic,
  outcomeText,
  timeoutMs,
  cursorTimeoutMs,
  attempts,
  recovered,
  waitOutSave,
}: BandagerOptions): Bandager => {
  const { all, outcomeFor } = outcomeVocabulary(outcomeText);

  let ranOut: string | undefined;

  // The pack rather than the world: findType with no source would happily return a bandage lying on
  // the floor, or one in somebody else's hands, and using it would open a cursor over nothing.
  const inPack = (): Item | Mobile | undefined =>
    client.findType(graphic, undefined, player.backpack?.serial);

  const applyOnce = (): boolean => {
    const bandages = inPack();

    if (!bandages) {
      ranOut = 'no bandages left in the pack';

      return false;
    }

    // A cursor left open by anything before this would swallow the use
    target.cancel();

    journal.clear();
    player.use(bandages.serial);

    if (!target.waitTargetSelf(cursorTimeoutMs)) {
      log(`${prefix}: no target cursor for the bandage`);

      return false;
    }

    const before = player.hits;

    // One wait for the whole application: the sentence that says it finished and the sentence that
    // says it never started both land inside it.
    const matched = journal.waitForTextAny(all, undefined, timeoutMs);
    const outcome = matched ? outcomeFor(matched) : undefined;

    if (outcome === 'noBandages') {
      ranOut = 'the shard says there are no bandages';

      return false;
    }

    if (outcome === 'saving') {
      waitOutSave();
    }

    // The hits are the proof, exactly as the mana is for a cast: a shard whose wordings this table
    // has wrong still heals, and a shard that says it healed while nothing moved has not.
    return player.hits > before || outcome === 'healed';
  };

  return {
    empty: () => ranOut,

    mend: () => {
      if (recovered()) {
        return true;
      }

      if (ranOut) {
        return false;
      }

      log(`${prefix}: ${player.hits}/${player.maxHits} hits, bandaging`);

      for (let attempt = 1; attempt <= attempts && !ranOut; attempt++) {
        applyOnce();

        if (recovered()) {
          log(`${prefix}: healed to ${player.hits}/${player.maxHits}`);

          return true;
        }

        if (player.isDead) {
          break;
        }
      }

      if (ranOut) {
        log(`${prefix}: ${ranOut}`);
      }

      return false;
    },
  };
};
