import { now } from '../lib/clock.js';
import { distanceTo, hex } from '../lib/entity.js';
import { createScan, createTileStore, type Tile as BlockedTile } from '../lib/tiles.js';
import {
  MINE_RANGE,
  NOT_ORE_GRAPHICS,
  ORE_STATIC_NAME,
  ORE_TILE_GRAPHICS,
  RESPAWN_DELAY,
  SCAN_RADIUS,
  UNREACHABLE_DELAY,
} from './config.js';
import { memory } from './memory.js';

export interface Tile extends BlockedTile {
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

// Land and static tiledata are numbered in separate tables, so the same number means different
// things depending on which one it came from - 1339 is a mountain band as land and a cave floor as
// a static. Everything that keys on an art therefore keys on the kind as well.
const artKey = (graphic: number, isLand: boolean) => `${isLand ? 'land' : 'static'}:${graphic}`;

// A mountainside is land and a cave floor is a static, and only the static can be named: getTile
// answers with flags and no name at all. So land goes through the table in config and statics go
// through their name, the way lumberjacking finds trees.
export const isOre = (graphic: number, isLand: boolean): boolean => {
  // Refusals first, seeds second: ORE_TILE_GRAPHICS is a guess copied out of RunUO, and a ban is the
  // shard's own answer. Asked the other way round the seed outranks both and markNotMineable
  // silently does nothing.
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

const store = /* @__PURE__ */ createTileStore<Tile>({
  label: 'vein',
  blocked: () => memory().blocked,
  depletedFor: RESPAWN_DELAY,
  unreachableFor: UNREACHABLE_DELAY,
  depleted: 'is out of ore',
});

export const markDepleted = store.markDepleted;
export const markUnreachable = store.markUnreachable;
export const markUnusable = store.markUnusable;

// For the shard answering about where you stand rather than about a tile. Parks everything in reach
// on one cooldown so the loop walks off; marking a single tile leaves the character swinging at the
// spot the shard has just written off, for the same sentence, until the run gives up.
export const markAreaDepleted = (range: number): number => {
  const until = now() + RESPAWN_DELAY;
  let parked = 0;

  for (let dx = -range; dx <= range; dx++) {
    for (let dy = -range; dy <= range; dy++) {
      for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
        if (!isOre(tile.graphic, tile.isLand)) {
          continue;
        }

        store.block(
          { x: tile.x, y: tile.y, z: tile.z, graphic: tile.graphic, isLand: tile.isLand },
          until,
        );
        parked++;
      }
    }
  }

  log(
    `vein: nothing harvestable at ${player.x},${player.y}, parking ${parked} tile(s) ` +
      `within ${range} for ${Math.max(1, Math.round(RESPAWN_DELAY / 60_000))}m`,
  );

  return parked;
};

// About the art, not the tile: a wrong entry in ORE_TILE_GRAPHICS is a whole band of the mountain,
// and learning it one tile at a time would cost a walk each. Takes the whole tile because the ban
// has to name which tiledata table the number came from - see artKey.
export const markNotMineable = (tile: Tile): void => {
  const { notOre } = memory();
  const key = artKey(tile.graphic, tile.isLand);

  if (notOre.has(key)) {
    return;
  }

  notOre.add(key);
  log(`vein: ${hex(tile.graphic)} cannot be mined, skipping that art from here on`);
};

const scan = /* @__PURE__ */ createScan<Tile>({
  label: 'scanForVein',
  radius: SCAN_RADIUS,
  blocked: () => memory().blocked,
  matches: isOre,

  // Land is not skipped the way lumberjacking skips it - a mountainside *is* land, and it is the
  // ordinary case rather than the exception
  describe: (vein) => `'${vein.isLand ? 'land' : (client.getStatic(vein.graphic)?.name ?? '?')}'`,
});

// The tile the loop is working, kept across cycles so the swing is not preceded by a box scan
let current: Vein | undefined;

// One getTerrainList against the (2 * SCAN_RADIUS + 1) squared the box costs. The z and the art have
// to match as well as the coordinates: a tile carries several, and only one of them is the vein.
const stillOre = (vein: Vein): Vein | undefined => {
  const until = store.blockedUntil(vein);

  if (until !== undefined && now() < until) {
    return undefined;
  }

  for (const tile of client.getTerrainList(vein.x, vein.y) ?? []) {
    if (tile.z === vein.z && tile.graphic === vein.graphic && tile.isLand === vein.isLand) {
      return isOre(tile.graphic, tile.isLand) ? { ...vein, distance: distanceTo(vein) } : undefined;
    }
  }

  return undefined;
};

// Widened rather than swept: a mountain face is wall-to-wall ore, so the tile that replaces a worked
// out one is almost always within reach, and the full box is 625 client calls to find it.
export const scanForVein = (): Scan => {
  if (current) {
    current = stillOre(current);

    if (current) {
      return { vein: current };
    }
  }

  const near = scan(MINE_RANGE);

  if (near.found) {
    current = near.found;

    return { vein: current };
  }

  const { found, readyAt } = scan();
  current = found;

  return { vein: found, respawnsAt: readyAt };
};
