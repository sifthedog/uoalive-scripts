import { now } from './clock.js';
import { distanceTo, hex } from './entity.js';
import type { Approach } from './harvest.js';

// Finding a tile, walking to it, and remembering what the shard said about it. What the harvest
// scripts do not share is how a tile is recognised as harvestable: lumberjacking asks the tiledata
// for a name, mining reads a table of land graphics.

// What it takes to name a tile in the block map, and no more. Mining extends this with `isLand`,
// because the two tiledata tables are numbered separately and its targeting depends on which one an
// art came from.
export interface Tile {
  x: number;
  y: number;
  z: number;
  graphic: number;
}

export interface Found<T extends Tile> {
  found?: T & { distance: number };

  // The soonest a tile that is only cooling down comes back. Undefined when nothing is waiting,
  // which is what tells an idle wait apart from an area with nothing left in it.
  readyAt?: number;
}

// Per tile, not per resource: a tree is several statics and only its trunk is harvestable, and a
// mountain face is a wall of tiles where one running dry says nothing about the one beside it.
const tileKey = (tile: Tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;

const minutes = (ms: number) => Math.max(1, Math.round(ms / 60_000));

export interface TileStore<T extends Tile> {
  block: (tile: T, until: number) => void;
  blockedUntil: (tile: T) => number | undefined;
  markDepleted: (tile: T) => void;
  markUnreachable: (tile: T) => void;
  markUnusable: (tile: T, reason: string) => void;
}

// Three failures, three meanings. Out of resource comes back after depletedFor; a walk that never
// closed after unreachableFor, because what blocked the path is usually a player or a pet rather
// than the tile; out of sight or an art that cannot be worked, never. A cooldown and a permanent ban
// being the same lookup is what keeps the scan's filter to one line.
export const createTileStore = <T extends Tile>(options: {
  label: string;
  blocked: () => Map<string, number>;
  depletedFor: number;
  unreachableFor: number;

  // How this script words a tile that has nothing left - 'is out of wood' / 'is out of ore'
  depleted: string;
}): TileStore<T> => {
  const block = (tile: T, until: number) => options.blocked().set(tileKey(tile), until);

  return {
    block,
    blockedUntil: (tile) => options.blocked().get(tileKey(tile)),

    markDepleted: (tile) => {
      block(tile, now() + options.depletedFor);
      log(
        `${options.label}: ${tile.x},${tile.y} ${options.depleted}, ` +
          `back in ${minutes(options.depletedFor)}m`,
      );
    },

    markUnreachable: (tile) => {
      block(tile, now() + options.unreachableFor);
      log(
        `${options.label}: ${tile.x},${tile.y} could not be walked to, ` +
          `retrying in ${minutes(options.unreachableFor)}m`,
      );
    },

    markUnusable: (tile, reason) => {
      block(tile, Infinity);
      log(`${options.label}: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
    },
  };
};

// Read against the player rather than against the other tile: the question is whether the character
// can get to it, and the character is what moves.
export const withinZOf = (z: number, allowed: number): boolean => Math.abs(z - player.z) <= allowed;

// Every distinct graphic a scan settles on is named once, not just the first: the first one it locks
// onto may well be scenery, and then the console would never name the art that does work.
export const createScan = <T extends Tile>(options: {
  label: string;
  radius: number;
  blocked: () => Map<string, number>;
  matches: (graphic: number, isLand: boolean) => boolean;

  // Lumberjacking skips land outright - a tree is a static. Mining does not: a mountainside *is*
  // land, and it is the ordinary case rather than the exception.
  skipLand?: boolean;

  // Lumberjacking filters out tiles no legal standing spot can reach, so a tree outside the box is
  // never picked, walked at, refused and only then written off. Mining has no box.
  reachable?: (x: number, y: number) => boolean;

  // Mining only: a mountain face 40 z above you passes the 2D distance test and the walk never closes
  withinZ?: number;

  describe: (tile: T & { distance: number }) => string;
}) => {
  const reported = new Set<number>();

  return (radius = options.radius): Found<T> => {
    const blocked = options.blocked();
    const time = now();

    let best: (T & { distance: number }) | undefined;
    let readyAt: number | undefined;

    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          if (options.skipLand && tile.isLand) {
            continue;
          }

          // Undefined rather than falsy, or a tolerance of 0 would read as no tolerance at all
          if (options.withinZ !== undefined && !withinZOf(tile.z, options.withinZ)) {
            continue;
          }

          if (!options.matches(tile.graphic, tile.isLand)) {
            continue;
          }

          if (options.reachable && !options.reachable(tile.x, tile.y)) {
            continue;
          }

          // The tile carries its own coordinates; trust those over the ones we scanned with.
          // `isLand` is copied across whether or not T declares it - for lumberjacking it is an
          // unread extra rather than a wrong one.
          const candidate = {
            x: tile.x,
            y: tile.y,
            z: tile.z,
            graphic: tile.graphic,
            isLand: tile.isLand,
            distance: distanceTo(tile),
          } as unknown as T & { distance: number };

          const key = tileKey(candidate);
          const until = blocked.get(key);

          if (until !== undefined) {
            if (time < until) {
              // Infinity never arrives, so only a tile genuinely coming back is worth waiting for
              if (Number.isFinite(until) && (readyAt === undefined || until < readyAt)) {
                readyAt = until;
              }
              continue;
            }

            // Dropped as it expires rather than left to accumulate: this map outlives the run
            blocked.delete(key);
          }

          if (!best || candidate.distance < best.distance) {
            best = candidate;
          }
        }
      }
    }

    // Named as they come up, so a wrong match is visible in the console rather than silent flailing
    if (best && !reported.has(best.graphic)) {
      log(`${options.label}: matching ${hex(best.graphic)} ${options.describe(best)}`);
      reported.add(best.graphic);
    }

    return { found: best, readyAt };
  };
};

// Scan, then either swing at what was found, take a step toward it, or wait for it to come back.
export const createApproach = <T extends Tile>(options: {
  scan: () => Found<T>;
  range: number;
  maxSteps: number;
  step: (target: T & { distance: number }) => boolean;
  markUnreachable: (target: T & { distance: number }) => void;
  idleUntil: (at: number) => void;

  // A step during a save does not move you, which is what this reads as a wall
  isSaving?: () => boolean;

  // The stop reason for an area with nothing left in it, and the one chance to say what was on the
  // ground instead
  nothingFound: () => string;
}) => {
  // Steps spent on the tile currently being walked to, reset when the target changes
  let walkingTo: string | undefined;
  let steps = 0;

  return (): Approach<T & { distance: number }> => {
    const { found, readyAt } = options.scan();

    if (!found) {
      if (readyAt === undefined) {
        return { stop: options.nothingFound() };
      }

      options.idleUntil(readyAt);

      return { waited: true };
    }

    if (found.distance <= options.range) {
      walkingTo = undefined;

      return { target: found };
    }

    // Coarser than the block map's key on purpose: a tile carries several arts, and once one is
    // written off the next is the same walk. Two *different* targets taking turns as nearest still
    // reset it - the stall watchdog is what bounds that.
    const key = `${found.x},${found.y}`;
    if (key !== walkingTo) {
      walkingTo = key;
      steps = 0;
    }

    // Blocked or out of patience: set the tile aside, or the next scan picks the same one again. Not
    // during a save, where a step that does not move cost a live run two good veins for five minutes.
    if ((!options.step(found) && !options.isSaving?.()) || ++steps > options.maxSteps) {
      options.markUnreachable(found);
      walkingTo = undefined;
    }

    return { walked: true };
  };
};
