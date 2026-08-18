// Swings a tool at a resource until something stops the run. Everything the shipped harvesters
// disagree about comes in through the call - nothing here reads a config.

import { backoffFor, type StallWatch } from './loop.js';

export interface HarvestTimings {
  stepDelay: number;
  maxCycles: number;

  // A wrong OUTCOME_TEXT trips this immediately, which is the point: better to stop and be told than
  // to flail at a tile for an hour.
  maxUnknown: number;

  maxThrottled: number;

  // Generous like maxThrottled rather than tight like maxUnknown, because this is a shard declining
  // to start an action and not a script that cannot read one: a run once ended on five of these in
  // fifteen seconds with a pickaxe plainly in hand.
  maxNoCursor: number;

  logEvery: number;
  throttleBackoff: number;
  throttleBackoffMax: number;
}

// A cycle spent on something other than a swing, or an ending. Undefined carries on to the swing.
export type Interlude = { phase: string } | { stop: string } | undefined;

// What a script's own outcome handler answers with. Undefined means it did not recognise the
// outcome, and the runner counts it unreadable.
export type Handled = { stop?: string } | undefined;

// Waiting is not walking: a resource coming back is the script working, so that one path leaves the
// stall watchdog alone. See StallWatch.endCycle.
export type Approach<T> = { target: T } | { walked: true } | { waited: true } | { stop: string };

export interface HarvestOptions<T> {
  prefix: string;

  // The outcome that means a swing landed, and the noun for the tool in the worn-out line
  landed: string;
  toolName: string;

  stopReason: () => string | undefined;

  // Noticing trouble and shouting about it. Returns nothing on purpose: what it sees is never a
  // reason to stop, and the run has one way out already.
  watch?: () => void;

  equipTool: () => boolean;

  // Mining's dismount, which is a step rather than a precondition because the fire beetle is both
  // the ride and the smelter. Answers with the reason the run cannot go on.
  ready?: () => string | undefined;

  // The weight backstop: smelt the ore, or put the logs on the animal
  relieve?: () => Interlude;

  // Absent for a script that swings where it stands
  approach?: () => Approach<T>;

  harvest: (target?: T) => string | undefined;

  // Runs before the shared counters, so a swing's produce is in the pack by the time anything reads
  // the pack
  onLanded?: () => void;

  handle: (outcome: string, target?: T) => Handled;

  // The body of the every-logEvery line: '12 swings, 40 ore'
  progress: (tally: number) => string;

  // The run's own last word, before the stop reason is said and handed to exit
  finish?: (tally: number, reason: string) => void;

  waitOutSave: () => void;
  stall: StallWatch;

  timings: HarvestTimings;
}

export const runHarvest = <T>({
  prefix,
  landed,
  toolName,
  stopReason,
  watch,
  equipTool,
  ready,
  relieve,
  approach,
  harvest,
  onLanded,
  handle,
  progress,
  finish,
  waitOutSave,
  stall,
  timings,
}: HarvestOptions<T>): void => {
  let tally = 0;
  let unknown = 0;
  let stop: string | undefined;

  // Compared against rather than `tally % logEvery`, which is a property of the count and not of the
  // cycle - so it stays true for every cycle after the twenty-fifth swing.
  let reported = 0;

  let throttled = 0;

  // Counted apart from `unknown`, which it used to share: a refusal is not an outcome the script
  // failed to read, and spending that budget on one ended a live run in fifteen seconds with a tool
  // plainly in hand.
  let noCursor = 0;

  const endCycle = (phase: string, cycle: number): void => {
    stall.endCycle(phase, cycle, tally);
    stop ??= stall.reason();
  };

  for (let cycle = 0; cycle < timings.maxCycles && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }

    watch?.();

    // Asked every cycle rather than once at the start, so a remount or a broken tool costs a single
    // cycle instead of the rest of the run.
    stop = ready?.();
    if (stop) {
      break;
    }

    if (!equipTool()) {
      stop = `no ${toolName}`;
      break;
    }

    const relieved = relieve?.();

    if (relieved) {
      if ('stop' in relieved) {
        stop = relieved.stop;
        break;
      }

      endCycle(relieved.phase, cycle);
      sleep(timings.stepDelay);
      continue;
    }

    let target: T | undefined;

    if (approach) {
      const found = approach();

      if ('stop' in found) {
        stop = found.stop;
        break;
      }

      // Walking sleeps inside the step rather than here, where a resource coming back has already
      // waited out its own clock
      if ('waited' in found) {
        continue;
      }

      if ('walked' in found) {
        endCycle('walking', cycle);
        continue;
      }

      target = found.target;
    }

    const outcome = harvest(target);

    if (outcome === landed) {
      tally++;
      unknown = 0;
      throttled = 0;
      stall.progressed();
      onLanded?.();
    } else {
      switch (outcome) {
        case 'wornOut':
          log(`${prefix}: ${toolName} worn out, swapping`);
          unknown = 0;
          break;

        // The counters are reset rather than left alone, because whatever they had accumulated was
        // measured against a server that was not answering. The stall watchdog goes with them: a
        // shard that saves often would otherwise walk a run to its stop a save at a time.
        case 'saving':
          waitOutSave();
          unknown = 0;
          throttled = 0;
          stall.progressed();
          break;

        case 'throttled':
          throttled++;

          // A refusal is a read outcome, so it clears the unreadable count: left standing, a shard
          // alternating refusals with silence ends the run on maxUnknown without ever producing five
          // unreadable cycles in a row.
          unknown = 0;
          log(`${prefix}: shard says wait (${throttled}/${timings.maxThrottled}), backing off`);
          sleep(backoffFor(throttled, timings.throttleBackoff, timings.throttleBackoffMax));

          if (throttled >= timings.maxThrottled) {
            stop = 'the shard kept refusing the swing';
          }
          break;

        // With a tool demonstrably in hand this is the shard declining to start the swing, which on
        // a live run was a third of them. The swing has already looked for a reason, so this is a
        // refusal with nothing said about it - backed off like one, on a budget of its own.
        case 'noCursor':
          noCursor++;
          log(`${prefix}: no target cursor (${noCursor}/${timings.maxNoCursor}), backing off`);
          sleep(backoffFor(noCursor, timings.throttleBackoff, timings.throttleBackoffMax));

          if (noCursor >= timings.maxNoCursor) {
            stop = 'the shard never opened a target cursor';
          }
          break;

        default: {
          const handled = outcome === undefined ? undefined : handle(outcome, target);

          if (handled) {
            unknown = 0;
            stop ??= handled.stop;
          } else {
            unknown++;
            log(
              `${prefix}: unreadable outcome (${unknown}/${timings.maxUnknown}), check OUTCOME_TEXT`,
            );
          }
        }
      }
    }

    // Done here rather than inside each branch the way `unknown` is: every branch but one clears it,
    // and one added later would have to remember to.
    if (outcome !== 'noCursor') {
      noCursor = 0;
    }

    if (unknown >= timings.maxUnknown) {
      stop = `${timings.maxUnknown} unreadable outcomes in a row`;
      break;
    }

    if (tally >= reported + timings.logEvery) {
      reported = tally;
      log(`${prefix}: ${progress(tally)}, ${player.weight}/${player.weightMax}`);
    }

    endCycle(outcome ?? 'unknown', cycle);
    sleep(timings.stepDelay);
  }

  const reason = stop ?? `hit the ${timings.maxCycles} cycle backstop`;

  finish?.(tally, reason);

  // Said through log as well as handed to exit, because how the client renders an exit message is
  // its own business and the reason a run ended must not be the line that gets away
  log(`${prefix}: stopping - ${reason}`);
  exit(`${prefix}: ${reason}`);
};
