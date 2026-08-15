import { packContents } from './containers.js';
import { overweight } from './weight.js';

// Anything a guard returns ends the run, and the string it returns is what says why. Composed per
// folder rather than shared whole, because which checks apply is a property of what the script does
// to the pack: a crafting script fills it, and boxes/ empties it onto the floor, so the same
// overweight check that protects one stops the other on exactly the character it would have relieved.
export type Guard = () => string | undefined;

export const dead: Guard = () => (player.isDead ? 'you are dead' : undefined);

// Buffer, so the stop lands before the shard starts refusing to move the new item
export const heavy =
  (buffer: number): Guard =>
  () =>
    overweight(buffer) ? `overweight (${player.weight}/${player.weightMax})` : undefined;

export const packFull =
  (limit: number): Guard =>
  () => {
    const top = (packContents() ?? []).length;

    return top >= limit ? `pack is full (${top} items at the top level)` : undefined;
  };

// Order is the caller's, and it matters: death comes first everywhere, so a corpse is never
// reported as merely overweight.
export const firstReason = (...guards: Guard[]): string | undefined => {
  for (const guard of guards) {
    const reason = guard();
    if (reason) {
      return reason;
    }
  }

  return undefined;
};
