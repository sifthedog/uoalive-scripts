import { hex } from './entity.js';
import { countsByGraphic, diffCounts, type Change, type Counts } from './pack.js';

// Turning one resource into another - logs into boards, ore into ingots. Stock RunUO answers with a
// sound and no message either way, so the pack diff is the only evidence a conversion landed, and
// that same diff names the output's art whatever this shard numbers it.

export interface Converter {
  // Hues given up on, which is what keeps `nextStack`'s candidates shrinking and the pass count down
  writtenOff: Set<number>;

  // Returns whether the pack is clear of everything convertible. False means it stopped early - a
  // save, or the pass backstop - and the caller decides whether to come back.
  run: () => boolean;

  // Written off is not the same as impossible: a target that stepped out of range, a run of throttled
  // attempts and a stack that was briefly too small all look alike. Declines once a retry has been
  // spent with nothing converting since, which is what stops a caller that hauls the leftovers from
  // looping - `force` is for a caller that never ships the input raw and so must always reconsider.
  retry: (force?: boolean) => boolean;
}

export const createConverter = (options: {
  // Names every log line this makes, e.g. 'makeBoards' / 'smelt'
  label: string;

  // How the log lines describe what a written-off hue stays as: 'leaving it as logs'
  leftAs: string;

  attempts: number;
  timeoutMs: number;
  pollMs: number;
  delayMs: number;
  maxPasses: number;
  unskilledText: string[];

  // Silent in the pack diff and therefore indistinguishable from a material that cannot be worked, so
  // without this a run of busy moments writes off a good hue - which on a live mining run cost 86 ore
  // of a single colour.
  throttledText?: string[];

  isSaving: () => boolean;

  // Anything else that makes this pass hopeless without saying anything about the material: a fire
  // beetle that has wandered off, a forge left behind. Asked only once a stack has been chosen, so a
  // pack with nothing to convert never needs the target to exist.
  notNow?: () => string | undefined;

  // Rescanned every pass rather than planned up front: a conversion consumes the stack and creates a
  // new item, so every other serial in a snapshot goes stale the moment the first one converts.
  nextStack: (writtenOff: Set<number>) => Item | undefined;

  // Says why nothing was eligible when the pack still holds some. 'smelting freed nothing' over a
  // pack with ore in it is an accusation without evidence.
  describeSkipped?: (writtenOff: Set<number>) => string | undefined;

  // Returns false only for a cursor that never opened - everything else is judged by the pack diff.
  perform: (stack: Item) => boolean;

  // Graphics already accounted for, so the diff does not "learn" the input as an output
  known: () => Set<number>[];

  // Where a newly learned output graphic goes, and what to call it in the line that says so
  learn: (graphic: number) => void;
  learned: string;
}): Converter => {
  const writtenOff = new Set<number>();

  // Silent misses per hue, cleared by a success, so only a hue that fails repeatedly is given up on
  const misses = new Map<number, number>();

  // Whether anything has converted since the last retry. `run` refills the written-off set every
  // call, so a retry granted unconditionally answers true again on the next cycle and the caller
  // loops - which in mining is hours of 'smelting' phases before the stall watchdog ends the run.
  let progressed = true;

  // Every failing path has to come through here: one that returned without counting leaves the
  // candidate set unchanged, so the next pass picks the same stack and the loop runs to its backstop
  // instead of shrinking.
  const missed = (hue: number): void => {
    const count = (misses.get(hue) ?? 0) + 1;
    misses.set(hue, count);

    if (count >= options.attempts) {
      writtenOff.add(hue);
      log(`${options.label}: hue ${hue} failed ${count} times, ${options.leftAs}`);
    }
  };

  const learnOutput = (changes: Change[]): void => {
    for (const { key, delta } of changes) {
      if (delta <= 0) {
        continue;
      }

      const graphic = Number(key.split('/')[0]);
      if (options.known().some((set) => set.has(graphic))) {
        continue;
      }

      options.learn(graphic);
      log(`${options.label}: ${options.learned} is ${hex(graphic)}`);
    }
  };

  // The action throttle can hold a conversion well past any pause worth taking, and reading too early
  // is indistinguishable from a resource that cannot be worked - which is how ordinary logs ended up
  // on the pack animal.
  const waitForChange = (before: Counts): Change[] => {
    for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
      sleep(options.pollMs);

      const changes = diffCounts(before, countsByGraphic());
      if (changes.length > 0) {
        return changes;
      }
    }

    return [];
  };

  // `perform` clears the journal, so a save that starts mid-attempt is past the check at the top of
  // the pass: one cost three hues and ended a live run overweight beside a working beetle.
  const saving = (hue: number): boolean => {
    if (!options.isSaving()) {
      return false;
    }

    log(`${options.label}: the world is saving, not counting it against hue ${hue}`);

    return true;
  };

  const convertOne = (stack: Item): void => {
    const hue = stack.hue ?? 0;
    const before = countsByGraphic();

    if (!options.perform(stack)) {
      if (saving(hue)) {
        return;
      }

      // Counted like any other failure. Without this an empty hand - dead tool, just broken,
      // mid-swap - spends every pass waiting on a cursor that is never going to come.
      missed(hue);
      return;
    }

    const changes = waitForChange(before);
    if (changes.length > 0) {
      misses.delete(hue);
      progressed = true;
      learnOutput(changes);
      return;
    }

    // Asked before either wording, because a frozen shard's verdict on the material is worthless
    if (saving(hue)) {
      return;
    }

    // Nothing was attempted, so this is not a verdict on the material: left uncounted the way a world
    // save is. Checked before the unskilled wordings only because it is the commoner of the two.
    if (options.throttledText?.some((text) => journal.containsText(text))) {
      log(`${options.label}: the shard says wait, not counting it against hue ${hue}`);
      return;
    }

    // A material that needs a skill you do not have is not something retrying supplies.
    if (options.unskilledText.some((text) => journal.containsText(text))) {
      writtenOff.add(hue);
      log(`${options.label}: not skilled enough for hue ${hue}, ${options.leftAs}`);
      return;
    }

    // Otherwise it was silent, which is also what a throttled or stale attempt looks like
    missed(hue);
  };

  return {
    writtenOff,

    run: () => {
      for (let pass = 0; pass < options.maxPasses; pass++) {
        // A frozen shard answers a conversion the same way an unworkable material does - with nothing
        // at all - so without this a world save costs `attempts` and writes the hue off for the rest
        // of the run. Left for the caller: the pack is still heavy, so it comes back.
        if (options.isSaving()) {
          log(`${options.label}: the world is saving, leaving it for now`);
          return false;
        }

        const stack = options.nextStack(writtenOff);

        if (!stack) {
          const skipped = options.describeSkipped?.(writtenOff);
          if (skipped) {
            log(`${options.label}: ${skipped}`);
          }
          return true;
        }

        // Asked only once there is something that needs it: a pack with nothing to convert is
        // finished rather than blocked, which is why smeltAll can be called every time a vein dries.
        const blocked = options.notNow?.();
        if (blocked) {
          log(`${options.label}: ${blocked}, leaving it for now`);
          return false;
        }

        convertOne(stack);
        sleep(options.delayMs);
      }

      // Termination does not rest on this: a hue either converts or is given up on after `attempts`,
      // so the candidate set always shrinks.
      log(`${options.label}: hit the ${options.maxPasses} pass backstop`);
      return false;
    },

    retry: (force = false) => {
      if (writtenOff.size === 0 || (!progressed && !force)) {
        return false;
      }
      progressed = false;

      log(`${options.label}: giving ${writtenOff.size} hue(s) written off earlier another go`);
      writtenOff.clear();
      misses.clear();

      return true;
    },
  };
};
