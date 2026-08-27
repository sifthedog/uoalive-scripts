export type Verdict = 'idle' | 'moved' | 'quiet';

// A pass that shifted some of what it issued is 'moved': a throttled pass comes back partial, and
// the stragglers go next cycle
export const verdictFor = (issued: number, landedStacks: number): Verdict =>
  issued === 0 ? 'idle' : landedStacks > 0 ? 'moved' : 'quiet';

export interface Quiet {
  saw: (verdict: Verdict) => number;
  reset: () => void;
  reason: (left: number) => string | undefined;
}

// Deliberately not createStallWatch: its contract is cycles that were meant to make progress, and a
// watch with nothing to move was not.
export const createQuiet = (max: number): Quiet => {
  let count = 0;

  return {
    saw: (verdict) => {
      if (verdict === 'quiet') {
        count++;
      } else if (verdict === 'moved') {
        count = 0;
      }

      return count;
    },

    // For the branches that were never the script's fault - a world save refuses every move it
    // catches, and counting those walks a run to its stop a save at a time
    reset: () => {
      count = 0;
    },

    reason: (left) =>
      count >= max
        ? `${max} passes in a row moved nothing, with ${left} still in the pack`
        : undefined,
  };
};
