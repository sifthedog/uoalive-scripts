import { isOre } from './vein.js';

// What is actually on the ground around you, and which of it the config matches. A run that exits
// saying 'no ore in range' while standing on a mountain has told you nothing you can act on; the
// useful question is which arts it saw and rejected.

export interface Art {
  graphic: number;
  isLand: boolean;
  flags: number;
  tiles: number;
  name: string;
  matches: boolean;
}

export const surveyTerrain = (radius: number): Art[] => {
  // Keyed on graphic *and* isLand: the two tiledata tables are numbered separately.
  const seen = new Map<string, Art>();

  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
        const key = `${tile.graphic}/${tile.isLand}`;
        const already = seen.get(key);

        if (already) {
          already.tiles++;
          continue;
        }

        seen.set(key, {
          graphic: tile.graphic,
          isLand: tile.isLand,
          flags: tile.flags,
          tiles: 1,
          name: tile.isLand ? '' : (client.getStatic(tile.graphic)?.name ?? '?'),
          matches: isOre(tile.graphic, tile.isLand),
        });
      }
    }
  }

  // Commonest first: whatever tops this list while you stand on a mountain face is almost certainly
  // what you came to mine.
  return [...seen.values()].sort((a, b) => b.tiles - a.tiles);
};

// Decimal as well as hex, because the RunUO tables ORE_TILE_GRAPHICS is seeded from are decimal.
export const describeArt = (art: Art): string => {
  const kind = art.isLand ? 'land' : `static '${art.name}'`;
  const mark = art.matches ? 'MATCHES' : '-';

  return (
    `${art.graphic} (0x${art.graphic.toString(16)}) ${kind}, ` +
    `flags 0x${art.flags.toString(16)}, ${art.tiles} tiles, ${mark}`
  );
};

export const reportTerrain = (radius: number, limit = Infinity): Art[] => {
  const found = surveyTerrain(radius);

  log(`survey: ${found.length} distinct arts within ${radius} tiles of ${player.x},${player.y}`);

  for (const art of found.slice(0, limit)) {
    log(`survey: ${describeArt(art)}`);
  }

  if (found.length > limit) {
    log(`survey: ${found.length - limit} rarer arts not shown`);
  }

  return found;
};
