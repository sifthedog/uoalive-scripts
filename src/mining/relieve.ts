import type { Interlude } from '../lib/harvest.js';
import { overweight } from '../lib/weight.js';
import { groupOres, oreTotal } from './ore.js';
import { isSaving, waitOutSave } from './save.js';
import { retryUnsmeltable } from './smelt.js';

// The weight backstop both mining runs share. Ore weighs twelve stones and an ingot almost nothing
// and there is nowhere else for the weight to go, so a smelt that frees nothing is an ending.

// No buffer: ore travels as ore until it cannot travel at all.
export const tooHeavy = (): boolean => overweight();

export const createSmeltForRoom = (options: {
  smelt: () => boolean;

  // What the stop line adds after 'smelting freed nothing' - the stationary run has advice to give
  hint?: string;
}): (() => Interlude) => {
  const stop = (): Interlude => ({
    stop:
      `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, ` +
      'and smelting freed nothing' +
      (options.hint ? ` - ${options.hint}` : ''),
  });

  return () => {
    if (!tooHeavy()) {
      return undefined;
    }

    const before = oreTotal();

    // Unconditional, because the decision has already been taken: a helper that asked tooHeavy() a
    // second time could disagree, and the run stopped for weight without ever having tried.
    groupOres();
    options.smelt();

    // Ore leaving the pack is the proof, not the weight going down: the client can still report its
    // pre-smelt figure over a conversion the pack diff has confirmed, and that ended live runs.
    if (oreTotal() < before) {
      return { phase: 'smelting' };
    }

    // Before the retry rather than after it: a frozen shard converts nothing, and a retry spent here
    // is the run's only one gone, which is exactly how a save ended a run 14 stones over the limit.
    if (isSaving()) {
      waitOutSave();

      return { phase: 'smelting' };
    }

    // A beetle briefly out of range looks exactly like an ore that cannot be worked. False once a
    // retry has been spent freeing nothing, or this cycles in 'smelting' until the stall watchdog.
    if (retryUnsmeltable()) {
      return { phase: 'smelting' };
    }

    // The last thing tried rather than a second helping of the first: the retry above has just
    // reopened the hues written off, so this pass is the one that can act on them.
    groupOres();
    options.smelt();

    if (oreTotal() < before) {
      return { phase: 'smelting' };
    }

    // A save that arrived during either pass, checked where the verdict would otherwise be drawn
    if (isSaving()) {
      waitOutSave();

      return { phase: 'smelting' };
    }

    return stop();
  };
};
