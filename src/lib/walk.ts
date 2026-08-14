// There is no pathfinding call in this API - player.run takes one direction at a time - so this
// steps naively and watches whether it actually moved.

// RunUO's offsets. Directions.Right/Down/Left/Up are the diagonals NE/SE/SW/NW.
const DIRECTION_BY_STEP = new Map([
  ['0,-1', Directions.North],
  ['1,-1', Directions.Right],
  ['1,0', Directions.East],
  ['1,1', Directions.Down],
  ['0,1', Directions.South],
  ['-1,1', Directions.Left],
  ['-1,0', Directions.West],
  ['-1,-1', Directions.Up],
]);

// `constrain` is the one place a box has to be enforced, because this is the one place the character
// moves. Lumberjacking passes allowedStep, which slides along the box edge rather than giving up;
// mining passes nothing, because it roams and what keeps a run somewhere sensible is where the ore
// is, not a rectangle.
export const createStepToward = (options: {
  delayMs: number;
  constrain?: (stepX: number, stepY: number) => [number, number] | undefined;
}) => {
  // Named `spot` rather than `target` because `target` is the ambient cursor global, and shadowing
  // it here would be a trap for whoever next adds a target.cancel() to this file.
  return (spot: { x: number; y: number }): boolean => {
    const wantX = Math.sign(spot.x - player.x);
    const wantY = Math.sign(spot.y - player.y);

    const step = options.constrain
      ? options.constrain(wantX, wantY)
      : wantX === 0 && wantY === 0
        ? undefined
        : ([wantX, wantY] as [number, number]);

    if (step === undefined) {
      return false;
    }

    const direction = DIRECTION_BY_STEP.get(`${step[0]},${step[1]}`);

    if (direction === undefined) {
      return false;
    }

    const beforeX = player.x;
    const beforeY = player.y;

    // Issued twice on purpose: a step in a direction you are not already facing only turns you
    player.run(direction);
    sleep(options.delayMs);
    player.run(direction);
    sleep(options.delayMs);

    return player.x !== beforeX || player.y !== beforeY;
  };
};
