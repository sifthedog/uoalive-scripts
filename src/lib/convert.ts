import { hex } from './entity.js';
import { countsByGraphic, diffCounts, type Change, type Counts } from './pack.js';

// Turning one resource into another - logs into boards, ore into ingots - is the same job twice.
// Stock RunUO answers with a sound and no message either way, so the pack diff is the only evidence
// a conversion landed, and that same diff names the output's art whatever this shard numbers it.
//
// What differs is only the gesture: boards are the tool used and the resource targeted, smelting is
// the ore double-clicked and the beetle targeted. That is `perform`.

export interface Converter {
  // Hues this run has given up on. Lumberjacking's haul reads it to decide which logs travel as
  // logs; nothing outside mining reads its equivalent.
  writtenOff: Set<number>;

  // Returns whether the pack is clear of everything convertible. False means it stopped early -
  // a save, or the pass backstop - and the caller decides whether to come back.
  run: () => boolean;

  // Written off is not the same as impossible. A few silent passes is a thin basis for carrying a
  // hue home: a target that stepped out of range, a run of throttled attempts and a stack that was
  // briefly too small all look exactly like a resource that cannot be worked. When the alternative
  // is ending the run overweight, this clears the verdicts for one more go - and returns false once
  // there is nothing left to reconsider, which is what keeps it from looping.
  retry: () => boolean;
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

  isSaving: () => boolean;

  // The next stack worth attempting, or undefined when there is nothing left. Rescanned every pass
  // rather than planned up front: a conversion consumes the stack and creates a new item, so every
  // other serial in a snapshot goes stale the moment the first one converts.
  nextStack: (writtenOff: Set<number>) => Item | undefined;

  // Says why nothing was eligible when the pack still holds some. 'smelting freed nothing' over a
  // pack with ore in it is an accusation without evidence.
  describeSkipped?: (writtenOff: Set<number>) => string | undefined;

  // The gesture. Returns false only for a cursor that never opened - everything else is judged by
  // the pack diff, not by this.
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

  // Counts one failure against a hue and gives up on it once they add up. Every failing path has to
  // come through here: one that returned without counting leaves the candidate set unchanged, so the
  // next pass picks the same stack and the loop runs to its backstop instead of shrinking.
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

  // Watch the pack rather than sleeping a fixed amount and reading once. The action throttle can
  // hold a conversion well past any pause worth taking, and reading too early is indistinguishable
  // from a resource that cannot be worked - which is how ordinary logs ended up on the pack animal.
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

  const convertOne = (stack: Item): void => {
    const hue = stack.hue ?? 0;
    const before = countsByGraphic();

    if (!options.perform(stack)) {
      // Counted like any other failure. Without this an empty hand - dead tool, just broken,
      // mid-swap - spends every pass of the loop waiting on a cursor that is never going to come.
      missed(hue);
      return;
    }

    const changes = waitForChange(before);
    if (changes.length > 0) {
      misses.delete(hue);
      learnOutput(changes);
      return;
    }

    // The shard saying it outright is worth acting on immediately; a material that needs a skill you
    // do not have is not something retrying supplies.
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
        // A frozen shard answers a conversion the same way an unworkable material does - with
        // nothing at all - so without this a world save costs `attempts` and the hue is written off
        // for the rest of the run. Left for the caller: the pack is still heavy, so it comes back.
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

        convertOne(stack);
        sleep(options.delayMs);
      }

      // Termination does not rest on this: a hue either converts or is given up on after `attempts`,
      // so the candidate set always shrinks. This is the backstop.
      log(`${options.label}: hit the ${options.maxPasses} pass backstop`);
      return false;
    },

    retry: () => {
      if (writtenOff.size === 0) {
        return false;
      }

      log(`${options.label}: giving ${writtenOff.size} hue(s) written off earlier another go`);
      writtenOff.clear();
      misses.clear();

      return true;
    },
  };
};
