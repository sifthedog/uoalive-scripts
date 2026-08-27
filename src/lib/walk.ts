import { STEPS, type Step } from './grid.js';

// One direction at a time is all player.run takes, so this steps and watches whether it actually
// moved. Where to step is lib/grid.ts's job.

// RunUO's numbering, in grid.ts's clockwise-from-north order. Directions.Right/Down/Left/Up are the
// diagonals NE/SE/SW/NW rather than the cardinals their names suggest.
const DIRECTIONS = [
  Directions.North,
  Directions.Right,
  Directions.East,
  Directions.Down,
  Directions.South,
  Directions.Left,
  Directions.West,
  Directions.Up,
];

const indexOf = (step: Step): number =>
  STEPS.findIndex(([x, y]) => x === step[0] && y === step[1]);

// `constrain` is the one place a box has to be enforced, because this is the one place the character
// moves. Lumberjacking passes allowedStep, which slides along the box edge rather than giving up;
// mining passes `route`, because it roams and what keeps a run somewhere sensible is where the ore
// is, not a rectangle.
export const createStepToward = (options: {
  delayMs: number;
  constrain?: (stepX: number, stepY: number) => [number, number] | undefined;
  route?: (spot: { x: number; y: number }) => Step | undefined;
}) => {
  const take = (step: Step): boolean => {
    const allowed = options.constrain ? options.constrain(step[0], step[1]) : step;

    if (allowed === undefined) {
      return false;
    }

    const at = indexOf(allowed);

    if (at < 0) {
      return false;
    }

    const beforeX = player.x;
    const beforeY = player.y;

    // Issued twice on purpose: a step in a direction you are not already facing only turns you
    player.run(DIRECTIONS[at]);
    sleep(options.delayMs);
    player.run(DIRECTIONS[at]);
    sleep(options.delayMs);

    return player.x !== beforeX || player.y !== beforeY;
  };

  // Named `spot` rather than `target` because `target` is the ambient cursor global, and shadowing
  // it here would be a trap for whoever next adds a target.cancel() to this file.
  return (spot: { x: number; y: number }): boolean => {
    const wantX = Math.sign(spot.x - player.x);
    const wantY = Math.sign(spot.y - player.y);

    const wanted =
      options.route?.(spot) ??
      (wantX === 0 && wantY === 0 ? undefined : ([wantX, wantY] as Step));

    if (wanted === undefined) {
      return false;
    }

    if (take(wanted)) {
      return true;
    }

    // A pet or another player parked in the gap is not in the terrain, so a step that did not move
    // tries either side of itself before the caller writes the tile off
    const at = indexOf(wanted);

    return (
      at >= 0 && [STEPS[(at + 1) % STEPS.length], STEPS[(at + 7) % STEPS.length]].some(take)
    );
  };
};
