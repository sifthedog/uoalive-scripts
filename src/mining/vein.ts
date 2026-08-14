import {
  NOT_ORE_GRAPHICS,
  ORE_STATIC_NAME,
  ORE_TILE_GRAPHICS,
  RESPAWN_DELAY,
  SCAN_RADIUS,
  UNREACHABLE_DELAY,
} from './config.js';
import { memory, now } from './memory.js';

export interface Tile {
  x: number;
  y: number;
  z: number;
  graphic: number;

  // Carried because the *targeting* depends on it, not the search: target.terrain picks the land
  // tile when no graphic is passed and the static standing on it when one is. See dig.ts.
  isLand: boolean;
}

export interface Vein extends Tile {
  distance: number;
}

export interface Scan {
  vein?: Vein;

  // The soonest a tile that is only cooling down comes back. Undefined when nothing is waiting to
  // respawn, which is what tells an idle wait apart from a mountain with nothing left in it.
  respawnsAt?: number;
}

// getStatic reads the client's own tiledata, so the answer never changes. The scan asks about the
// same handful of graphics hundreds of times a cycle, so remember them.
const known = new Map<number, boolean>();

const tileKey = (tile: Tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;

const minutes = (ms: number) => Math.max(1, Math.round(ms / 60_000));

// Land and static tiledata are numbered in separate tables, so the same number means different
// things depending on which one it came from - 1339 is a mountain band as land and a cave floor as
// a static. Everything that keys on an art therefore keys on the kind as well.
const artKey = (graphic: number, isLand: boolean) => `${isLand ? 'land' : 'static'}:${graphic}`;

// A mountainside is a land tile and a cave floor is a static, and the two are identified in
// different ways because the client only names one of them: getStatic reads the static tiledata,
// and getTile - the land one - answers with flags and no name at all. So land tiles go through the
// table in config and statics go through their name, the way lumberjacking finds trees.
export const isOre = (graphic: number, isLand: boolean): boolean => {
  // Refusals first, seeds second. ORE_TILE_GRAPHICS is a guess copied out of RunUO; a ban is either
  // the shard's own answer, learned at the cost of a walk and a swing, or a hand-written correction
  // to that guess. Asked the other way round - as lumberjacking can afford to, since its seed sets
  // are empty - the seed outranks both and markNotMineable silently does nothing at all.
  if (NOT_ORE_GRAPHICS.has(graphic) || memory().notOre.has(artKey(graphic, isLand))) {
    return false;
  }

  // No name to fall back on, so the table is the whole answer for land
  if (isLand) {
    return ORE_TILE_GRAPHICS.has(graphic);
  }

  const remembered = known.get(graphic);
  if (remembered !== undefined) {
    return remembered;
  }

  const name = client.getStatic(graphic)?.name ?? '';
  const matches = ORE_STATIC_NAME.test(name);
  known.set(graphic, matches);

  return matches;
};

// Keyed per tile: a mountain face is a wall of them, and one running dry says nothing about the
// tile beside it.
const block = (tile: Tile, until: number) => memory().blocked.set(tileKey(tile), until);

// A vein comes back, so this is a cooldown rather than a write-off. Timed from the swing that
// emptied it, so the tile returns on its own and the same face can be worked all day.
export const markDepleted = (tile: Tile): void => {
  block(tile, now() + RESPAWN_DELAY);
  log(`vein: ${tile.x},${tile.y} is out of ore, back in ${minutes(RESPAWN_DELAY)}m`);
};

// The area version, for the shard answering about where you stand rather than about a tile - which
// is the only kind of answer a swing that names no tile can get. Parks everything in reach on the
// same cooldown, so the next scan has to look further afield and the loop walks somewhere else.
// Marking a single tile instead leaves the character standing exactly where the shard has just said
// there is nothing, swinging again for the same sentence until the run gives up on it.
export const markAreaDepleted = (range: number): number => {
  const until = now() + RESPAWN_DELAY;
  let parked = 0;

  for (let dx = -range; dx <= range; dx++) {
    for (let dy = -range; dy <= range; dy++) {
      for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
        if (!isOre(tile.graphic, tile.isLand)) {
          continue;
        }

        block(
          { x: tile.x, y: tile.y, z: tile.z, graphic: tile.graphic, isLand: tile.isLand },
          until,
        );
        parked++;
      }
    }
  }

  log(
    `vein: nothing harvestable at ${player.x},${player.y}, parking ${parked} tile(s) ` +
      `within ${range} for ${minutes(RESPAWN_DELAY)}m`,
  );

  return parked;
};

// A path that never closed says nothing about the vein, only about what was standing in it, so this
// one is timed too - and it has to be, now that a write-off outlives the run that made it.
export const markUnreachable = (tile: Tile): void => {
  block(tile, now() + UNREACHABLE_DELAY);
  log(`vein: ${tile.x},${tile.y} could not be walked to, retrying in ${minutes(UNREACHABLE_DELAY)}m`);
};

// For the refusals that waiting cannot fix: out of line of sight, or a tile the shard will not
// mine. Infinity rather than a long cooldown, so the scan never spends a swing on it again.
export const markUnusable = (tile: Tile, reason: string): void => {
  block(tile, Infinity);
  log(`vein: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
};

// "You can't mine that" is about the art, not the tile: a wrong entry in ORE_TILE_GRAPHICS is a
// whole band of the mountain, and learning it one tile at a time would cost a walk each. Contrast
// markDepleted, which is per tile because a vein comes back and its neighbour may still be full.
// Takes the whole tile rather than its graphic because the ban has to name which tiledata table
// the number came from - see artKey.
export const markNotMineable = (tile: Tile): void => {
  const { notOre } = memory();
  const key = artKey(tile.graphic, tile.isLand);

  if (notOre.has(key)) {
    return;
  }

  notOre.add(key);
  log(`vein: 0x${tile.graphic.toString(16)} cannot be mined, skipping that art from here on`);
};

// Every distinct graphic the scan settles on, not just the first: the first one it locks onto may
// well be scenery, and then the console would never name the art that does work.
const reportedGraphics = new Set<number>();

// Chebyshev, because that is how the shard measures range: a diagonal step covers both axes
const distanceTo = (x: number, y: number) =>
  Math.max(Math.abs(x - player.x), Math.abs(y - player.y));

export const scanForVein = (): Scan => {
  const { blocked } = memory();
  const time = now();

  let best: Vein | undefined;
  let respawnsAt: number | undefined;

  for (let dx = -SCAN_RADIUS; dx <= SCAN_RADIUS; dx++) {
    for (let dy = -SCAN_RADIUS; dy <= SCAN_RADIUS; dy++) {
      for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
        // Land is not skipped here the way lumberjacking skips it - a mountainside *is* land, and
        // it is the ordinary case rather than the exception
        if (!isOre(tile.graphic, tile.isLand)) {
          continue;
        }

        // The tile carries its own coordinates; trust those over the ones we scanned with
        const vein: Vein = {
          x: tile.x,
          y: tile.y,
          z: tile.z,
          graphic: tile.graphic,
          isLand: tile.isLand,
          distance: distanceTo(tile.x, tile.y),
        };

        const key = tileKey(vein);
        const until = blocked.get(key);

        if (until !== undefined) {
          if (time < until) {
            // Infinity never arrives, so only a tile that is genuinely coming back is worth waiting for
            if (Number.isFinite(until) && (respawnsAt === undefined || until < respawnsAt)) {
              respawnsAt = until;
            }
            continue;
          }

          // Dropped as it expires rather than left to accumulate: this map outlives the run
          blocked.delete(key);
        }

        if (!best || vein.distance < best.distance) {
          best = vein;
        }
      }
    }
  }

  // Named as they come up, so a wrong match is visible in the console rather than silent flailing
  if (best && !reportedGraphics.has(best.graphic)) {
    const name = best.isLand ? 'land' : (client.getStatic(best.graphic)?.name ?? '?');
    log(`scanForVein: matching 0x${best.graphic.toString(16)} '${name}'`);
    reportedGraphics.add(best.graphic);
  }

  return { vein: best, respawnsAt };
};
