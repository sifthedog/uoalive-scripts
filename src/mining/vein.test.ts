import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, terrainMap, tile, type FakeWorld } from '../test-support/uo.js';
import { IMPASSABLE } from '../lib/flags.js';
import { RESPAWN_DELAY, UNREACHABLE_DELAY } from './config.js';

// A land graphic inside the seeded RunUO bands, and one well outside them
const MOUNTAIN = 231;
const GRASS = 3;

// Statics, which are matched by name instead. CAVE is deliberately a number that also falls inside
// a seeded land band: the two tiledata tables are numbered separately, and a static must not be
// matched by the land table just because its number appears there.
const CAVE = 1339;
const CHAIR = 0x0b4e;

// Cooldowns are wall-clock, so the clock is frozen here and moved by hand
const START = Date.parse('2026-08-14T12:00:00Z');

let world: FakeWorld;

// vein.ts memoizes every static it has resolved, so each test needs its own copy of the module.
//
// The blocked tiles and the banned arts live on globalThis, which vi.resetModules() does NOT clear
// - that is the whole point of memory.ts, and it makes every test inherit the last one's mountain
// unless forget() is called here, before vein.ts has a chance to load the store.
const loadVein = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    ...config,
  }));

  (await import('./memory.js')).forget();

  return import('./vein.js');
};

// getTerrainList is asked about one column at a time, so the fake answers per coordinate
const terrainFrom = (tiles: ReturnType<typeof tile>[]) =>
  vi.fn((x: number, y: number) => tiles.filter((t) => t.x === x && t.y === y));

const land = (fields: { x: number; y: number; z?: number; graphic?: number }) =>
  tile({ graphic: MOUNTAIN, isLand: true, ...fields });

afterEach(() => {
  vi.useRealTimers();
});

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  vi.useFakeTimers();
  vi.setSystemTime(START);
  world = installGlobals({
    player: { x: 100, y: 100 },
    client: {
      getStatic: vi.fn((graphic: number) =>
        graphic === CAVE ? { name: 'cave floor' } : { name: 'a wooden chair' },
      ),
    } as never,
  });
});

// A vein is only somewhere to stand next to, so ore behind a wall is ore the run cannot have. The
// flood is squeezed down to the size of the picture, or a route slips out through the unloaded
// terrain around it - which is passable on purpose, see lib/grid.ts.
describe('ore the character cannot walk to', () => {
  const WALLED = { ROUTE_RADIUS: 4, SCAN_RADIUS: 4 };

  const drawn = (rows: string[]) => {
    world.client.getTerrainList = terrainMap([96, 96], rows, {
      '#': { isLand: true, flags: IMPASSABLE },
      M: { isLand: true, graphic: MOUNTAIN },
    });
  };

  it('picks the vein on this side of a wall over the nearer one behind it', async () => {
    drawn([
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.M...#.M.',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
    ]);

    const { scanForVein } = await loadVein(WALLED);

    expect(scanForVein().vein).toMatchObject({ x: 97, y: 100 });
  });

  it('counts what it dropped, so a run walled in can say why it found nothing', async () => {
    drawn([
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#.M.',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#...',
    ]);

    const { scanForVein, skippedAsUnreachable } = await loadVein(WALLED);

    expect(scanForVein().vein).toBeUndefined();
    expect(skippedAsUnreachable()).toBe(1);
  });

  // The straight line says the walled vein is nearer; the walk round through the gap says it is not
  it('measures nearest by the length of the walk, not by the straight line', async () => {
    drawn([
      '....M#...',
      '.....#...',
      '.....#...',
      '.....#...',
      '.....#.M.',
      '.....#...',
      '.....#...',
      '.....#...',
      '.........',
    ]);

    const { scanForVein } = await loadVein(WALLED);

    expect(scanForVein().vein).toMatchObject({ x: 100, y: 96, distance: 4 });
  });
});

describe('isOre', () => {
  // The whole reason this differs from lumberjacking's isTree: getStatic reads the *static*
  // tiledata, so a land tile has no name to test and the table in config is the only answer
  it('identifies a land tile from the table without asking the client for a name', async () => {
    const { isOre } = await loadVein();

    expect(isOre(MOUNTAIN, true)).toBe(true);
    expect(world.client.getStatic).not.toHaveBeenCalled();
  });

  it('rejects a land tile the table does not list, rather than guessing at it', async () => {
    const { isOre } = await loadVein();

    expect(isOre(GRASS, true)).toBe(false);
    expect(world.client.getStatic).not.toHaveBeenCalled();
  });

  it('identifies a static by its tiledata name', async () => {
    const { isOre } = await loadVein();

    expect(isOre(CAVE, false)).toBe(true);
  });

  it('rejects a static whose name says nothing about rock', async () => {
    const { isOre } = await loadVein();

    expect(isOre(CHAIR, false)).toBe(false);
  });

  it('treats a static the client knows nothing about as not ore', async () => {
    world.client.getStatic.mockReturnValue(undefined);
    const { isOre } = await loadVein();

    expect(isOre(0x1234, false)).toBe(false);
  });

  // getStatic reads the client's own tiledata, so the answer never changes, and the scan asks about
  // the same handful of graphics hundreds of times a cycle
  it('asks the client once per static and remembers the answer', async () => {
    const { isOre } = await loadVein();

    isOre(CAVE, false);
    isOre(CAVE, false);
    isOre(CAVE, false);

    expect(world.client.getStatic).toHaveBeenCalledTimes(1);
  });

  // The land table is a guess copied out of RunUO, so it must lose to anything that actually knows
  // better - or a wrong band cannot be corrected from either the config or the shard
  it('does not match a static just because the land table holds its number', async () => {
    const { isOre } = await loadVein();

    expect(isOre(CAVE, true)).toBe(true);

    world.client.getStatic.mockReturnValue({ name: 'a wooden chair' });

    expect(isOre(CAVE, false)).toBe(false);
  });

  describe('config overrides', () => {
    it('rejects a graphic listed in NOT_ORE_GRAPHICS even though the table lists it', async () => {
      const { isOre } = await loadVein({ NOT_ORE_GRAPHICS: new Set([MOUNTAIN]) });

      expect(isOre(MOUNTAIN, true)).toBe(false);
    });

    it('accepts a land tile listed in ORE_TILE_GRAPHICS', async () => {
      const { isOre } = await loadVein({ ORE_TILE_GRAPHICS: new Set([GRASS]) });

      expect(isOre(GRASS, true)).toBe(true);
    });
  });
});

describe('markNotMineable', () => {
  // A wrong entry in the seeded table is a whole band of the mountain, so the ban is per art and
  // costs one walk to learn rather than one per tile
  it('drops every tile of that art from the scan at once', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 }), land({ x: 104, y: 100 })]);
    const { markNotMineable, scanForVein } = await loadVein();

    markNotMineable({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

    expect(scanForVein().vein).toBeUndefined();
  });

  // The other half of the separately-numbered-tables problem: banning land 1339 must not also ban
  // the cave floor static that happens to carry the same number
  it('bans the art in the table it came from and not its namesake in the other', async () => {
    const { isOre, markNotMineable } = await loadVein();

    markNotMineable({ x: 102, y: 100, z: 0, graphic: CAVE, isLand: true });

    expect(isOre(CAVE, true)).toBe(false);
    expect(isOre(CAVE, false)).toBe(true);
  });

  it('says so once and stays quiet on a repeat', async () => {
    const { markNotMineable } = await loadVein();

    markNotMineable({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });
    markNotMineable({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

    expect(world.log).toHaveBeenCalledTimes(1);
  });

  // The ban is learned on the shard and costs a walk and a swing to learn, so it goes into the
  // store that outlives the run rather than back into the config's seed
  it('survives a restart of the script', async () => {
    const { markNotMineable } = await loadVein();
    markNotMineable({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

    vi.resetModules();
    const { isOre } = await import('./vein.js');

    expect(isOre(MOUNTAIN, true)).toBe(false);
  });
});

describe('scanForVein', () => {
  it('finds nothing in empty terrain', async () => {
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toBeUndefined();
  });

  it('finds a vein and reports its distance', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 103, y: 100 })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toMatchObject({ x: 103, y: 100, graphic: MOUNTAIN, distance: 3 });
  });

  // Where mining and lumberjacking part company: a mountainside *is* land, so the land tiles the
  // chop scan throws away are the ordinary case here
  it('takes land tiles rather than skipping them', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toMatchObject({ x: 101, y: 100, isLand: true });
  });

  // dig.ts targets a static by graphic and land without one, so a scan that lost this flag would
  // send every swing at the wrong one of the two things standing on the tile
  it('carries isLand through to the vein it returns', async () => {
    world.client.getTerrainList = terrainFrom([tile({ x: 101, y: 100, graphic: CAVE })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toMatchObject({ graphic: CAVE, isLand: false });
  });

  it('prefers the nearer of two veins', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 108, y: 100 }), land({ x: 102, y: 100 })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein?.x).toBe(102);
  });

  // Chebyshev, because that is how the shard measures range: a diagonal step covers both axes, so
  // (103,103) is 3 away and not 6 - and closer than (105,100)
  it('measures distance the way the shard does', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 103, y: 103 }), land({ x: 105, y: 100 })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toMatchObject({ x: 103, y: 103, distance: 3 });
  });

  it('trusts the tile its own coordinates rather than the ones it scanned with', async () => {
    world.client.getTerrainList = vi.fn((x: number, y: number) =>
      x === 101 && y === 100 ? [land({ x: 105, y: 106, z: 7 })] : [],
    );
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toMatchObject({ x: 105, y: 106, z: 7 });
  });

  it('finds nothing beyond the scan radius', async () => {
    world.client.getTerrainList = terrainFrom([land({ x: 500, y: 500 })]);
    const { scanForVein } = await loadVein();

    expect(scanForVein().vein).toBeUndefined();
  });

  // The scan runs immediately before every swing, and the box is (2 * SCAN_RADIUS + 1) squared
  // client calls - enough of them to be the difference between the roaming script and mine-here
  // The swing names no tile - it answers the cursor with the character - so a vein is only somewhere
  // to stand. One up a cliff passes the 2D distance test and the walk at it never closes.
  describe('veins off the character\'s own level', () => {
    it('ignores one far above where the character stands', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100, z: 60 })]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().vein).toBeUndefined();
    });

    it('ignores one far below in the same way', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100, z: -60 })]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().vein).toBeUndefined();
    });

    it('prefers a further vein at your level to a nearer one up a cliff', async () => {
      world.client.getTerrainList = terrainFrom([
        land({ x: 101, y: 100, z: 60 }),
        land({ x: 105, y: 100 }),
      ]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().vein?.x).toBe(105);
    });

    // Without this an implementation comparing against a hardcoded 0 passes everything above
    it('measures the tolerance from the character rather than from zero', async () => {
      world.player.z = 58;
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100, z: 60 })]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().vein).toMatchObject({ x: 101, z: 60 });
    });

    it('takes 0 as exactly your level rather than as no tolerance at all', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100, z: 1 })]);
      const { scanForVein } = await loadVein({ MINE_Z_RANGE: 0 });

      expect(scanForVein().vein).toBeUndefined();
    });
  });

  describe('the tile already being worked', () => {
    it('re-reads it instead of sweeping the box again', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 })]);
      const { scanForVein } = await loadVein();

      scanForVein();
      world.client.getTerrainList.mockClear();

      expect(scanForVein().vein).toMatchObject({ x: 101, y: 100 });
      expect(world.client.getTerrainList).toHaveBeenCalledTimes(1);
    });

    it('gives it up once the art on it stops matching', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 })]);
      const { scanForVein } = await loadVein();

      scanForVein();
      world.client.getTerrainList = terrainFrom([tile({ x: 101, y: 100, graphic: GRASS })]);

      expect(scanForVein().vein).toBeUndefined();
    });

    // scanForVein hands `current` back before it scans at all, so the scan's own filter never sees it
    it('gives it up once the character is no longer at its level', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 })]);
      const { scanForVein } = await loadVein();

      scanForVein();
      world.player.z = 60;

      expect(scanForVein().vein).toBeUndefined();
    });

    it('gives it up once it is blocked, and finds the next one', async () => {
      world.client.getTerrainList = terrainFrom([
        land({ x: 101, y: 100 }),
        land({ x: 106, y: 100 }),
      ]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted(scanForVein().vein!);

      expect(scanForVein().vein?.x).toBe(106);
    });

    // A cached distance would leave the walk unable to tell it had arrived
    it('measures the distance again from where the character now stands', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 105, y: 100 })]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().vein?.distance).toBe(5);
      world.player.x = 104;

      expect(scanForVein().vein?.distance).toBe(1);
    });
  });

  describe('depleted veins', () => {
    it('stops returning a tile once it has run out of ore', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 }), land({ x: 106, y: 100 })]);
      const { markDepleted, scanForVein } = await loadVein();

      const first = scanForVein().vein!;
      expect(first.x).toBe(102);

      markDepleted(first);

      expect(scanForVein().vein?.x).toBe(106);
    });

    // What this whole map exists for: a face worked out by lunchtime is worth mining again by the
    // afternoon, and written off permanently the run runs out of mountain instead.
    it('offers the tile again once it has respawned', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted(scanForVein().vein!);
      expect(scanForVein().vein).toBeUndefined();

      vi.setSystemTime(START + RESPAWN_DELAY + 1);

      expect(scanForVein().vein?.x).toBe(102);
    });

    it('keeps it back until the cooldown is actually up', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted(scanForVein().vein!);

      vi.setSystemTime(START + RESPAWN_DELAY - 1000);

      expect(scanForVein().vein).toBeUndefined();
    });

    // What the loop waits on. Reported only when there is nothing to mine right now, and only for a
    // tile that is genuinely coming back.
    it('reports when the soonest cooling vein is due back', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted(scanForVein().vein!);

      expect(scanForVein().respawnsAt).toBe(START + RESPAWN_DELAY);
    });

    it('reports the soonest of several, not the last one it happened to see', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 }), land({ x: 106, y: 100 })]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted({ x: 106, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

      vi.setSystemTime(START + 60_000);
      markDepleted({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

      expect(scanForVein().respawnsAt).toBe(START + RESPAWN_DELAY);
    });

    it('has nothing to report while there is still a vein to mine', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { scanForVein } = await loadVein();

      expect(scanForVein().respawnsAt).toBeUndefined();
    });

    // A mountain face is a wall of tiles and one running dry says nothing about its neighbour, so
    // the key carries z and graphic as well as x and y
    it('drops one tile without dropping the art beside it', async () => {
      world.client.getTerrainList = terrainFrom([
        land({ x: 102, y: 100, z: 0 }),
        land({ x: 102, y: 100, z: 10, graphic: 232 }),
      ]);
      const { markDepleted, scanForVein } = await loadVein();

      markDepleted({ x: 102, y: 100, z: 0, graphic: MOUNTAIN, isLand: true });

      expect(scanForVein().vein).toMatchObject({ x: 102, y: 100, z: 10, graphic: 232 });
    });

    // 25 minutes outlasts most runs, so a restart that forgot would swing at everything it had just
    // emptied. The store is on globalThis for exactly this.
    it('stays depleted across a restart of the script', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const first = await loadVein();
      first.markDepleted(first.scanForVein().vein!);

      vi.resetModules();
      const { scanForVein } = await import('./vein.js');

      expect(scanForVein().vein).toBeUndefined();
    });
  });

  // Said about where you stand, not about a tile. Parking one vein would leave the character on a
  // spot the shard has just written off, swinging for the same sentence until the run gave up.
  describe('an area the shard says is empty', () => {
    it('parks every vein within reach, not just the nearest', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 }), land({ x: 102, y: 100 })]);
      const { markAreaDepleted, scanForVein } = await loadVein();

      expect(markAreaDepleted(2)).toBe(2);
      expect(scanForVein().vein).toBeUndefined();
    });

    // Which is what makes the character move: the next candidate is now out of MINE_RANGE, so the
    // loop walks to it rather than swinging where it stands
    it('leaves a vein beyond that reach to walk to', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 }), land({ x: 107, y: 100 })]);
      const { markAreaDepleted, scanForVein } = await loadVein();

      markAreaDepleted(2);

      expect(scanForVein().vein).toMatchObject({ x: 107, distance: 7 });
    });

    it('parks them on the same respawn cooldown as a vein worked out by hand', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 101, y: 100 })]);
      const { markAreaDepleted, scanForVein } = await loadVein();

      markAreaDepleted(2);

      expect(scanForVein().respawnsAt).toBe(START + RESPAWN_DELAY);

      vi.setSystemTime(START + RESPAWN_DELAY + 1);

      expect(scanForVein().vein?.x).toBe(101);
    });

    // The shard's sentence is about what it can reach, so a tile up a cliff is not one it spoke for
    it('leaves tiles off the character\'s level unparked', async () => {
      world.client.getTerrainList = terrainFrom([
        land({ x: 101, y: 100 }),
        land({ x: 101, y: 100, z: 60, graphic: 232 }),
      ]);
      const { markAreaDepleted } = await loadVein();

      expect(markAreaDepleted(2)).toBe(1);
    });

    it('ignores tiles that were never ore in the first place', async () => {
      world.client.getTerrainList = terrainFrom([
        land({ x: 101, y: 100 }),
        land({ x: 102, y: 100, graphic: GRASS }),
      ]);
      const { markAreaDepleted } = await loadVein();

      expect(markAreaDepleted(2)).toBe(1);
    });
  });

  describe('written-off veins', () => {
    // Line of sight and scenery: no amount of waiting makes either of them mineable
    it('never offers a tile marked unusable again', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markUnusable, scanForVein } = await loadVein();

      markUnusable(scanForVein().vein!, 'is not in line of sight');

      vi.setSystemTime(START + 24 * 60 * 60 * 1000);

      expect(scanForVein().vein).toBeUndefined();
    });

    // Or the loop would sit and wait for a tile that is never coming back
    it('is not something the loop is told to wait for', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markUnusable, scanForVein } = await loadVein();

      markUnusable(scanForVein().vein!, 'is not in line of sight');

      expect(scanForVein().respawnsAt).toBeUndefined();
    });

    // Timed rather than permanent: what blocked the path is usually a player or a pet, and this
    // write-off now outlives the run that made it
    it('retries a tile the walk could not close on', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markUnreachable, scanForVein } = await loadVein();

      markUnreachable(scanForVein().vein!);
      expect(scanForVein().vein).toBeUndefined();

      vi.setSystemTime(START + UNREACHABLE_DELAY + 1);

      expect(scanForVein().vein?.x).toBe(102);
    });

    it('gives up entirely once every candidate is spoken for', async () => {
      world.client.getTerrainList = terrainFrom([land({ x: 102, y: 100 })]);
      const { markUnusable, scanForVein } = await loadVein();

      markUnusable(scanForVein().vein!, 'cannot be mined');

      expect(scanForVein()).toEqual({ vein: undefined, respawnsAt: undefined });
    });
  });
});
