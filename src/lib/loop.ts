import { now } from './clock.js';
import type { Heartbeat } from './heartbeat.js';

export const minutes = (ms: number): number => Math.max(1, Math.round(ms / 60_000));

export const minutesLeft = (until: number): number => minutes(until - now());

// A fixed retry shorter than the shard's own timer re-arms the very throttle it is waiting out, so
// back off further each time - which both out-waits a real harvest delay within a couple of swings
// and self-tunes to the shard's pacing, since an action that lands resets the count.
export const backoffFor = (count: number, step: number, cap: number): number =>
  Math.min(step * count, cap);

// Nothing in reach right now, but something is coming back: wait for it rather than ending a run
// that only has to sit still to have a forest again.
//
// Sliced rather than slept through in one go, so the client stays responsive and the guards still
// get a look in - a quarter of an hour is long enough to be killed standing there, and one long
// sleep would carry on regardless. Bounded by the wait it was asked for as well as by the clock: a
// clock that does not advance would otherwise turn this into a spin.
export const createIdleWait = (options: {
  prefix: string;

  // How this script words what it is waiting on - 'everything in reach is regrowing'
  waitingFor: string;

  pollMs: number;
  logEveryMs: number;
  stopReason: () => string | undefined;
  onDone: () => void;
}) => {
  return (until: number): void => {
    const wait = until - now();
    if (wait <= 0) {
      return;
    }

    log(`${options.prefix}: ${options.waitingFor}, waiting ${minutesLeft(until)}m`);

    const slices = Math.ceil(wait / options.pollMs);
    let since = 0;

    for (let slice = 0; slice < slices && now() < until; slice++) {
      sleep(options.pollMs);
      since += options.pollMs;

      // Left to the loop to report and act on, so the wait has one way out and the run has one
      if (options.stopReason()) {
        return;
      }

      if (since >= options.logEveryMs) {
        since = 0;
        log(`${options.prefix}: ${minutesLeft(until)}m to go`);
      }
    }

    // This path reports on its own cadence, so start the next beat's interval from here rather than
    // letting one land on top of the line above
    options.onDone();
  };
};

export interface StallWatch {
  // Closes every cycle that was meant to make progress: says the run is alive whatever branch it
  // took, and counts the cycle against the watchdog. An idle wait is the one path that does not come
  // through here - it reports on its own cadence, and waiting for a resource to come back is the
  // script working, not the script stuck.
  endCycle: (phase: string, cycle: number, tally: number) => void;

  // Called by the branches that did make progress, and by the ones that were never the script's
  // fault - a world save is a pause, and counting it would walk a run to its stop a save at a time
  progressed: () => void;

  // Set once the watchdog has seen enough, and read by the loop as its stop reason
  reason: () => string | undefined;
}

export const createStallWatch = (options: {
  prefix: string;

  // How this script words what it is counting the absence of - 'cycles without a chop'
  without: string;

  warnAt: number;
  stopAt: number;
  heartbeat: Heartbeat;
}): StallWatch => {
  let since = 0;
  let reason: string | undefined;

  return {
    endCycle: (phase, cycle, tally) => {
      options.heartbeat.beat(phase, cycle, tally);
      since++;

      if (since === options.warnAt) {
        log(`${options.prefix}: ${options.warnAt} ${options.without}, last was '${phase}'`);
      }

      if (since >= options.stopAt) {
        reason = `no progress in ${options.stopAt} cycles, last was '${phase}'`;
      }
    },

    progressed: () => {
      since = 0;
    },

    reason: () => reason,
  };
};
