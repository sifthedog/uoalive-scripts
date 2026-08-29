import { distanceTo } from './entity.js';
import { BRIDGE, IMPASSABLE, SURFACE, WET } from './flags.js';

// Where the character can put its feet, and which way to step. There is no pathfinding or
// line-of-sight call in this API, but getTerrainList carries `flags` on every land tile and static,
// which is enough to tell a mountain face from the ground in front of it.

export type Step = [number, number];

export type Terrain = NonNullable<ReturnType<typeof client.getTerrainList>>;

// Clockwise from north, so the entries either side of a direction are its neighbours - which is what
// lets a blocked step slide rather than give up. lib/walk.ts maps these onto Directions.
export const STEPS: readonly Step[] = [
  [0, -1],
  [1, -1],
  [1, 0],
  [1, 1],
  [0, 1],
  [-1, 1],
  [-1, 0],
  [-1, -1],
];

// Known and blocked, against a coordinate the client has no terrain for at all. Every map
// coordinate has a land tile, so an empty answer means the chunk is not loaded - and refusing to
// walk on missing information is how a filter meant to stop bad walks starts stopping good ones.
const UNKNOWN = null;

export interface Grid {
  // Steps to the nearest spot the character could stand on within `range` of the tile, or undefined
  // when there is no way to it. The tile itself is usually a mountain face, which is exactly what
  // cannot be stood on.
  stepsTo: (spot: { x: number; y: number }, range: number) => number | undefined;

  routeTo: (spot: { x: number; y: number }, range: number) => Step | undefined;
  terrainAt: (x: number, y: number) => Terrain;
  describe: (radius: number) => string;

  // Tests only
  forget: () => void;
}

export const createGrid = (options: {
  radius: number;
  maxSteps: number;
  maxNodes: number;
  maxCells: number;

  // Z a single step may climb or drop. Symmetric on purpose: the goal-side flood below walks its
  // edges backwards, and an asymmetric rule there plans a climb the character cannot make.
  climb: number;

  // How far above and below a standing spot a solid art still counts as being in the way. The
  // typings carry no static height, so this is the whole of the approximation.
  height: number;
  headroom: number;

  // Where the character may put its feet at all, over and above the terrain: lumberjacking passes
  // its bounds box, so a route can never plan the step allowedStep would then refuse.
  passable?: (x: number, y: number) => boolean;
}): Grid => {
  // Land and statics do not change during a session, so a coordinate costs one getTerrainList for
  // the whole run - which is what makes a flood every cycle affordable next to the scan's own sweep
  const cells = new Map<string, number | undefined>();

  let unknowns = 0;
  let open = false;
  let saidOpen = false;

  const terrainAt = (x: number, y: number) => client.getTerrainList(x, y) ?? [];

  const standable = (entry: { flags: number; isLand: boolean }): boolean =>
    (entry.flags & (IMPASSABLE | WET)) === 0 &&
    (entry.isLand || (entry.flags & (SURFACE | BRIDGE)) !== 0);

  // The highest spot here a character could stand on, undefined for a wall, water or a mountain
  // face, and UNKNOWN for a coordinate the client could not answer for.
  const floorAt = (x: number, y: number): number | undefined | typeof UNKNOWN => {
    const key = `${x},${y}`;

    if (cells.has(key)) {
      return cells.get(key);
    }

    const entries = terrainAt(x, y);

    // Not cached: the chunk loads as the character walks into it, and a hole punched on the first
    // cycle would still be there twenty cycles later
    if (entries.length === 0) {
      unknowns++;

      return UNKNOWN;
    }

    let best: number | undefined;

    for (const entry of entries) {
      if (!standable(entry) || (best !== undefined && entry.z <= best)) {
        continue;
      }

      const buried = entries.some(
        (other) =>
          other !== entry &&
          (other.flags & IMPASSABLE) !== 0 &&
          other.z > entry.z - options.headroom &&
          other.z < entry.z + options.height,
      );

      if (!buried) {
        best = entry.z;
      }
    }

    // Cleared whole rather than evicted one at a time: a run roams, and re-reading what it needs
    // costs one cycle's calls
    if (cells.size >= options.maxCells) {
      cells.clear();
    }

    cells.set(key, best);

    return best;
  };

  // The z the character would arrive at, or undefined for a step it cannot take
  const stepZ = (x: number, y: number, fromZ: number): number | undefined => {
    if (options.passable && !options.passable(x, y)) {
      return undefined;
    }

    const z = floorAt(x, y);

    if (z === UNKNOWN) {
      return fromZ;
    }

    return z !== undefined && Math.abs(z - fromZ) <= options.climb ? z : undefined;
  };

  // The shard will not cut a corner between two blocked tiles, so neither does this, or every route
  // through a doorway comes back a step short
  const cornerOpen = (x: number, y: number, z: number, dx: number, dy: number): boolean =>
    dx === 0 ||
    dy === 0 ||
    (stepZ(x + dx, y, z) !== undefined && stepZ(x, y + dy, z) !== undefined);

  const inRange = (x: number, y: number): boolean =>
    Math.abs(x - player.x) <= options.radius && Math.abs(y - player.y) <= options.radius;

  // Breadth-first from a seed set, over cells keyed on x,y alone: a cave floor under a mountain
  // shelf is the one case that wants x,y,z, and it is not worth a priority queue.
  const flood = (seeds: { x: number; y: number; z: number }[]): Map<string, number> => {
    const cost = new Map<string, number>();
    const queue = [...seeds];

    for (const seed of seeds) {
      cost.set(`${seed.x},${seed.y}`, 0);
    }

    for (let head = 0; head < queue.length && cost.size < options.maxNodes; head++) {
      const from = queue[head];
      const steps = cost.get(`${from.x},${from.y}`)!;

      if (steps >= options.maxSteps) {
        continue;
      }

      for (const [dx, dy] of STEPS) {
        const x = from.x + dx;
        const y = from.y + dy;
        const key = `${x},${y}`;

        if (!inRange(x, y) || cost.has(key)) {
          continue;
        }

        const z = stepZ(x, y, from.z);

        if (z === undefined || !cornerOpen(from.x, from.y, from.z, dx, dy)) {
          continue;
        }

        cost.set(key, steps + 1);
        queue.push({ x, y, z });
      }
    }

    return cost;
  };

  // Every standable spot within `range` of the tile. Empty means nowhere to swing from.
  const spotsAround = (spot: { x: number; y: number }, range: number) => {
    const found: { x: number; y: number; z: number }[] = [];

    for (let dx = -range; dx <= range; dx++) {
      for (let dy = -range; dy <= range; dy++) {
        const x = spot.x + dx;
        const y = spot.y + dy;

        if (!inRange(x, y) || (options.passable && !options.passable(x, y))) {
          continue;
        }

        const z = floorAt(x, y);

        if (z !== undefined) {
          found.push({ x, y, z: z === UNKNOWN ? player.z : z });
        }
      }
    }

    return found;
  };

  // Standing somewhere this file calls impassable is proof the flags above are wrong for this shard,
  // so the filter turns itself off rather than reporting a world with nowhere to stand.
  const failedOpen = (): boolean => {
    if (!open && floorAt(player.x, player.y) === undefined) {
      open = true;

      if (!saidOpen) {
        saidOpen = true;
        log(
          'grid: the tile under your feet reads as impassable, so the walkability filter is off ' +
            'for this run - the flag values in lib/flags.ts are wrong for this shard',
        );
      }
    }

    return open;
  };

  let from: string | undefined;
  let reach = new Map<string, number>();
  let costs = new Map<string, number | undefined>();

  // Replanned whenever the character has moved, which is every step of a walk. Cheap after the first
  // pass: the terrain is cached, so this is map lookups and nothing else.
  const plan = (): Map<string, number> => {
    const here = `${player.x},${player.y},${player.z}`;

    if (from === here) {
      return reach;
    }

    from = here;
    costs = new Map();
    reach = flood([{ x: player.x, y: player.y, z: player.z }]);

    return reach;
  };

  const nearest = (spot: { x: number; y: number }, range: number): number | undefined => {
    const reached = plan();
    let best: number | undefined;

    for (let dx = -range; dx <= range; dx++) {
      for (let dy = -range; dy <= range; dy++) {
        const found = reached.get(`${spot.x + dx},${spot.y + dy}`);

        if (found !== undefined && (best === undefined || found < best)) {
          best = found;
        }
      }
    }

    return best;
  };

  return {
    terrainAt,

    stepsTo: (spot, range) => {
      if (failedOpen()) {
        return distanceTo(spot);
      }

      plan();

      const key = `${spot.x},${spot.y},${range}`;

      if (!costs.has(key)) {
        costs.set(key, nearest(spot, range));
      }

      return costs.get(key);
    },

    // Flooded from the goal rather than from the character, and read as a gradient: a breadth-first
    // walk out from the player reaches an open-ground tile by any of a dozen equal paths, and which
    // one it records decides the first step - so the character drifts diagonally down a corridor it
    // should walk straight along.
    routeTo: (spot, range) => {
      if (failedOpen()) {
        return undefined;
      }

      const seeds = spotsAround(spot, range);

      if (seeds.length === 0) {
        return undefined;
      }

      const cost = flood(seeds);
      let best: Step | undefined;
      let bestCost = cost.get(`${player.x},${player.y}`) ?? Infinity;

      if (bestCost === 0) {
        return undefined;
      }

      // The straight-line step first, and ties settled by whichever came first: on open ground every
      // step toward the goal is equally short, and this is what keeps the walk straight.
      const wanted: Step = [Math.sign(spot.x - player.x), Math.sign(spot.y - player.y)];
      const order = [wanted, ...STEPS];

      for (const [dx, dy] of order) {
        if (dx === 0 && dy === 0) {
          continue;
        }

        const found = cost.get(`${player.x + dx},${player.y + dy}`);

        if (found === undefined || found >= bestCost) {
          continue;
        }

        if (
          stepZ(player.x + dx, player.y + dy, player.z) === undefined ||
          !cornerOpen(player.x, player.y, player.z, dx, dy)
        ) {
          continue;
        }

        best = [dx, dy];
        bestCost = found;
      }

      return best;
    },

    describe: (radius) => {
      const reached = plan();
      unknowns = 0;

      let standing = 0;
      let blocked = 0;

      for (let dx = -radius; dx <= radius; dx++) {
        for (let dy = -radius; dy <= radius; dy++) {
          const z = floorAt(player.x + dx, player.y + dy);

          if (z === undefined) {
            blocked++;
          } else if (z !== UNKNOWN) {
            standing++;
          }
        }
      }

      const under = floorAt(player.x, player.y);

      return (
        `grid: within ${radius}, ${standing} tiles can be stood on and ${blocked} cannot, ` +
        `${unknowns} the client had no terrain for; ${reached.size} are walkable from here; ` +
        `under your feet ${under === UNKNOWN ? 'no terrain' : under === undefined ? 'IMPASSABLE - check lib/flags.ts' : `z ${under}`}`
      );
    },

    forget: () => {
      cells.clear();
      from = undefined;
      reach = new Map();
      costs = new Map();
      unknowns = 0;
      open = false;
      saidOpen = false;
    },
  };
};
