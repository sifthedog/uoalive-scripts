import { now } from './clock.js';
import { distanceTo, hex } from './entity.js';

// Both harvest scripts have to find a specific tile, walk to it, and remember what the shard said
// about it - which of those tiles are worth returning to, which are worth returning to later, and
// which never again. What they do not share is how a tile is recognised as harvestable at all:
// lumberjacking asks the tiledata for a name, mining reads a table of land graphics.

// What it takes to name a tile in the block map, and no more. Mining extends this with `isLand`,
// because the two tiledata tables are numbered separately and its targeting depends on which one an
// art came from; lumberjacking never needs to know, because a tree is always a static.
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

// Generic over the folder's own tile, which may carry more than the block key needs - mining's
// carries isLand - so callers can hand one straight over without stripping it first.
export interface TileStore<T extends Tile> {
  block: (tile: T, until: number) => void;
  markDepleted: (tile: T) => void;
  markUnreachable: (tile: T) => void;
  markUnusable: (tile: T, reason: string) => void;
}

// What the three failures mean is three different things, not one. Out of resource -> back after
// depletedFor. A walk that never closed -> back after unreachableFor, because what blocked the path
// is usually a player or a pet rather than the tile. Out of sight, out of shard-range, or an art
// that cannot be worked -> never again. A cooldown and a permanent ban being the same lookup is
// what keeps the scan's filter to one line.
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

  describe: (tile: T & { distance: number }) => string;
}) => {
  const reported = new Set<number>();

  return (): Found<T> => {
    const blocked = options.blocked();
    const time = now();

    let best: (T & { distance: number }) | undefined;
    let readyAt: number | undefined;

    for (let dx = -options.radius; dx <= options.radius; dx++) {
      for (let dy = -options.radius; dy <= options.radius; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          if (options.skipLand && tile.isLand) {
            continue;
          }

          if (!options.matches(tile.graphic, tile.isLand)) {
            continue;
          }

          if (options.reachable && !options.reachable(tile.x, tile.y)) {
            continue;
          }

          // The tile carries its own coordinates; trust those over the ones we scanned with.
          // `isLand` is copied across whether or not T declares it: mining reads it to decide how to
          // target, and for lumberjacking it is an unread extra rather than a wrong one.
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
