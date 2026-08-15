import { now } from './clock.js';

// Proof of life for a loop that can otherwise go quiet: a script standing still in silence looks
// exactly like a hung one.

export interface Heartbeat {
  beat: (phase: string, cycle: number, tally: number) => void;
  resetBeat: () => void;
}

// The clock, not the cycle counter, decides. A cycle can be 300ms or 8s depending on which waits it
// hit, so counting them would make the heartbeat's cadence a function of the fault.
export const createHeartbeat = (options: {
  prefix: string;
  noun: string;
  everyMs: number;
}): Heartbeat => {
  let lastBeat: number | undefined;

  return {
    beat: (phase, cycle, tally) => {
      const time = now();

      // First call sets the clock rather than logging: the run has just said what it is doing
      if (lastBeat === undefined) {
        lastBeat = time;
        return;
      }

      if (time - lastBeat < options.everyMs) {
        return;
      }

      lastBeat = time;
      log(
        `${options.prefix}: still here - ${phase}, cycle ${cycle}, at ${player.x},${player.y}, ` +
          `${player.weight}/${player.weightMax}, ${tally} ${options.noun}`,
      );
    },

    // For the paths that report on their own cadence, so the next beat is a full interval after they
    // stop rather than immediately on top of their last line
    resetBeat: () => {
      lastBeat = now();
    },
  };
};
