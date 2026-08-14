import { now } from '../lib/clock.js';
import { hex } from '../lib/entity.js';
import { createScan, createTileStore, type Tile as BlockedTile } from '../lib/tiles.js';
import {
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

export const scanForVein = (): Scan => {
  const { found, readyAt } = scan();

  return { vein: found, respawnsAt: readyAt };
};
