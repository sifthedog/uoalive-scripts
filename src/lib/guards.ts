import { packContents } from './containers.js';
import { hitsCeiling } from './vitals.js';
import { overweight } from './weight.js';

// Anything a guard returns ends the run, and the string is what says why. Composed per folder rather
// than shared whole: a crafting script fills the pack and boxes/ empties it onto the floor, so the
// same overweight check that protects one stops the other on the character it would have relieved.
export type Guard = () => string | undefined;

export const dead: Guard = () => (player.isDead ? 'you are dead' : undefined);

// Buffer, so the stop lands before the shard starts refusing to move the new item
export const heavy =
  (buffer: number): Guard =>
  () =>
    overweight(buffer) ? `overweight (${player.weight}/${player.weightMax})` : undefined;

// For a script whose own actions cost health - the necromancy trainer casts Pain Spike at itself -
// `dead` alone is a brake that only works once. Through hitsCeiling rather than player.maxHits so a
// stat refresh is not read as a character at death's door.
export const hurt =
  (fraction: number): Guard =>
  () => {
    const ceiling = hitsCeiling();

    if (ceiling === undefined) {
      return undefined;
    }

    return player.hits < ceiling * fraction ? `hurt (${player.hits}/${ceiling})` : undefined;
  };

export const packFull =
  (limit: number): Guard =>
  () => {
    const top = (packContents() ?? []).length;

    return top >= limit ? `pack is full (${top} items at the top level)` : undefined;
  };

// Order is the caller's, and it matters: death comes first everywhere, so a corpse is never reported
// as merely overweight.
export const firstReason = (...guards: Guard[]): string | undefined => {
  for (const guard of guards) {
    const reason = guard();
    if (reason) {
      return reason;
    }
  }

  return undefined;
};
