import { HEARTBEAT_EVERY } from './config.js';
import { now } from './memory.js';

// Proof of life for a loop that can otherwise go quiet. Most branches of the main loop say what
// they did, but the quiet ones - a swing that lands, a refusal that is only waited out - say
// nothing, and a script standing still in silence looks exactly like a hung one. This logs on a
// wall clock rather than per cycle, so a fast branch does not flood the console and a slow one
// still reports.

let lastBeat: number | undefined;

// The clock, not the cycle counter, decides. A cycle can be 300ms or 8s depending on which waits
// it hit, so counting them would make the heartbeat's cadence a function of the fault.
export const beat = (phase: string, cycle: number, chopped: number): void => {
  const time = now();

  // First call sets the clock rather than logging: the run has just said what it is doing
  if (lastBeat === undefined) {
    lastBeat = time;
    return;
  }

  if (time - lastBeat < HEARTBEAT_EVERY) {
    return;
  }

  lastBeat = time;
  log(
    `lumberjack: still here - ${phase}, cycle ${cycle}, at ${player.x},${player.y}, ` +
      `${player.weight}/${player.weightMax}, ${chopped} chops`,
  );
};

// For the paths that report on their own cadence, so the next beat is a full interval after they
// stop rather than immediately on top of their last line
export const resetBeat = (): void => {
  lastBeat = now();
};
