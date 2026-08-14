import { reachableFromBounds } from './bounds.js';
import {
  CHOP_RANGE,
  NOT_TREE_GRAPHICS,
  REGROW_DELAY,
  SCAN_RADIUS,
  TREE_GRAPHICS,
  UNREACHABLE_DELAY,
} from './config.js';
import { memory, now } from './memory.js';

export interface Tile {
  x: number;
  y: number;
  z: number;
  graphic: number;
}

export interface Tree extends Tile {
  distance: number;
}

export interface Scan {
  tree?: Tree;

  // The soonest a tile that is only cooling down comes back. Undefined when nothing is waiting to
  // regrow, which is what tells the loop apart from an idle wait from a wood with nothing left in it.
  regrowsAt?: number;
}

// getStatic reads the client's own tiledata, so the answer never changes. The scan asks about the
// same handful of graphics hundreds of times a cycle, so remember them.
const known = new Map<number, boolean>();

const tileKey = (tile: Tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;

const minutes = (ms: number) => Math.max(1, Math.round(ms / 60_000));

export const isTree = (graphic: number): boolean => {
  if (TREE_GRAPHICS.has(graphic)) {
    return true;
  }
  if (NOT_TREE_GRAPHICS.has(graphic) || memory().notTree.has(graphic)) {
    return false;
  }

  const remembered = known.get(graphic);
  if (remembered !== undefined) {
    return remembered;
  }

  const name = client.getStatic(graphic)?.name ?? '';
  const matches = /tree/i.test(name);
  known.set(graphic, matches);

  return matches;
};

// Keyed per tile, not per tree: a tree is several statics and only its trunk is harvestable, so the
// foliage has to drop out of the search one static at a time.
const block = (tile: Tile, until: number) => memory().blocked.set(tileKey(tile), until);

// A stump regrows, so this is a cooldown rather than a write-off. Timed from the swing that emptied
// it, so the tile comes back on its own and the same clearing can be worked all day.
export const markDepleted = (tile: Tile): void => {
  block(tile, now() + REGROW_DELAY);
  log(`tree: ${tile.x},${tile.y} is out of wood, back in ${minutes(REGROW_DELAY)}m`);
};

// A path that never closed says nothing about the tree, only about what was standing in it, so this
// one is timed too - and it has to be, now that a write-off outlives the run that made it.
export const markUnreachable = (tile: Tile): void => {
  block(tile, now() + UNREACHABLE_DELAY);
  log(`tree: ${tile.x},${tile.y} could not be walked to, retrying in ${minutes(UNREACHABLE_DELAY)}m`);
};

// For the refusals that waiting cannot fix: out of line of sight, or an art the shard will not
// harvest. Infinity rather than a long cooldown, so the scan never spends a swing on it again.
export const markUnusable = (tile: Tile, reason: string): void => {
  block(tile, Infinity);
  log(`tree: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
};

// "You can't use an axe on that" is about the graphic, not the tile: the tiledata calls a whole
// family of statics a tree, and only the trunk is harvestable. Banning the graphic drops every
// other tile of that art in one go, instead of learning the same thing tile by tile across the
// forest. Contrast markDepleted, which is per tile because a stump regrows and a neighbour of the
// same art may still have wood.
export const markNotHarvestable = (graphic: number): void => {
  const { notTree } = memory();

  if (notTree.has(graphic)) {
    return;
  }

  notTree.add(graphic);
  log(`tree: 0x${graphic.toString(16)} cannot be chopped, skipping that art from here on`);
};

// Every distinct graphic the scan settles on, not just the first: the first one it locks onto may
// well be scenery, and then the console would never name the art that does work.
const reportedGraphics = new Set<number>();

// Chebyshev, because that is how the shard measures range: a diagonal step covers both axes
const distanceTo = (x: number, y: number) =>
  Math.max(Math.abs(x - player.x), Math.abs(y - player.y));

export const scanForTree = (): Scan => {
  const { blocked } = memory();
  const time = now();

  let best: Tree | undefined;
  let regrowsAt: number | undefined;

  for (let dx = -SCAN_RADIUS; dx <= SCAN_RADIUS; dx++) {
    for (let dy = -SCAN_RADIUS; dy <= SCAN_RADIUS; dy++) {
      for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
        if (tile.isLand || !isTree(tile.graphic)) {
          continue;
        }

        // The tile carries its own coordinates; trust those over the ones we scanned with
        const tree: Tree = {
          x: tile.x,
          y: tile.y,
          z: tile.z,
          graphic: tile.graphic,
          distance: distanceTo(tile.x, tile.y),
        };

        // Asked before the cooldown rather than after it, for the same reason it is asked at all: a
        // tree no legal standing tile can reach is not one to walk to, and not one to wait for either
        if (!reachableFromBounds(tree.x, tree.y, CHOP_RANGE)) {
          continue;
        }

        const key = tileKey(tree);
        const until = blocked.get(key);

        if (until !== undefined) {
          if (time < until) {
            // Infinity never arrives, so only a tile that is genuinely coming back is worth waiting for
            if (Number.isFinite(until) && (regrowsAt === undefined || until < regrowsAt)) {
              regrowsAt = until;
            }
            continue;
          }

          // Dropped as it expires rather than left to accumulate: this map outlives the run
          blocked.delete(key);
        }

        if (!best || tree.distance < best.distance) {
          best = tree;
        }
      }
    }
  }

  // Named as they come up, so a wrong match is visible in the console rather than silent flailing
  if (best && !reportedGraphics.has(best.graphic)) {
    const name = client.getStatic(best.graphic)?.name ?? '?';
    log(`scanForTree: matching 0x${best.graphic.toString(16)} '${name}'`);
    reportedGraphics.add(best.graphic);
  }

  return { tree: best, regrowsAt };
};
