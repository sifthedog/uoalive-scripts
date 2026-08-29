import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { IMPASSABLE } from '../lib/flags.js';
import { installGlobals, tile, type FakeWorld } from '../test-support/uo.js';
import { REGROW_DELAY, ROAM_RADIUS, UNREACHABLE_DELAY } from './config.js';

const OAK = 0x0ce0;
const ROCK = 0x1771;

// Cooldowns are wall-clock, so the clock is frozen here and moved by hand
const START = Date.parse('2026-08-14T12:00:00Z');

let world: FakeWorld;

// tree.ts memoizes every graphic it has resolved, so each test needs its own copy of the module.
//
// The blocked tiles and the banned arts live on globalThis, which vi.resetModules() does NOT clear,
// so forget() has to be called here before tree.ts loads the store or every test inherits the last
// one's forest. BOUNDS defaults to undefined, because the checked-in box would hide every fixture.
const loadTree = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    BOUNDS: undefined,
    ...config,
  }));

  (await import('./memory.js')).forget();

  return import('./tree.js');
};

// getTerrainList is asked about one column at a time, so the fake answers per coordinate
const terrainFrom = (tiles: ReturnType<typeof tile>[]) =>
  vi.fn((x: number, y: number) => tiles.filter((t) => t.x === x && t.y === y));

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
        graphic === OAK ? { name: 'oak tree' } : { name: 'a rock' },
      ),
    } as never,
  });
});

describe('isTree', () => {
  it('identifies a tree by its tiledata name', async () => {
    const { isTree } = await loadTree();

    expect(isTree(OAK)).toBe(true);
  });

  it('rejects a static whose name says nothing about trees', async () => {
    const { isTree } = await loadTree();

    expect(isTree(ROCK)).toBe(false);
  });

  it('is case-insensitive about the name', async () => {
    world.client.getStatic.mockReturnValue({ name: 'Yew Tree' });
    const { isTree } = await loadTree();

    expect(isTree(0x1234)).toBe(true);
  });

  it('treats a static the client knows nothing about as not a tree', async () => {
    world.client.getStatic.mockReturnValue(undefined);
    const { isTree } = await loadTree();

    expect(isTree(0x1234)).toBe(false);
  });

  // getStatic reads the client's own tiledata, so the answer never changes, and the scan asks about
  // the same handful of graphics hundreds of times a cycle
  it('asks the client once per graphic and remembers the answer', async () => {
    const { isTree } = await loadTree();

    isTree(OAK);
    isTree(OAK);
    isTree(OAK);

    expect(world.client.getStatic).toHaveBeenCalledTimes(1);
  });

  it('remembers a negative answer too', async () => {
    const { isTree } = await loadTree();

    isTree(ROCK);
    isTree(ROCK);

    expect(world.client.getStatic).toHaveBeenCalledTimes(1);
  });

  describe('config overrides', () => {
    // The escape hatch for a shard whose names do not match: neither override should cost a lookup
    it('accepts a graphic listed in TREE_GRAPHICS without consulting tiledata', async () => {
      const { isTree } = await loadTree({ TREE_GRAPHICS: new Set([ROCK]) });

      expect(isTree(ROCK)).toBe(true);
      expect(world.client.getStatic).not.toHaveBeenCalled();
    });

    it('rejects a graphic listed in NOT_TREE_GRAPHICS even though tiledata calls it a tree', async () => {
      const { isTree } = await loadTree({ NOT_TREE_GRAPHICS: new Set([OAK]) });

      expect(isTree(OAK)).toBe(false);
      expect(world.client.getStatic).not.toHaveBeenCalled();
    });
  });
});

describe('markNotHarvestable', () => {
  // Per graphic, not per tile: the tiledata calls a whole family of statics a tree and only the
  // trunk is harvestable, so banning the art drops every tile of it at once
  it('stops the whole art from reading as a tree', async () => {
    const { isTree, markNotHarvestable } = await loadTree();

    expect(isTree(OAK)).toBe(true);

    markNotHarvestable(OAK);

    expect(isTree(OAK)).toBe(false);
  });

  it('drops every tile of that art from the scan at once', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 102, y: 100, graphic: OAK }),
      tile({ x: 104, y: 100, graphic: OAK }),
    ]);
    const { markNotHarvestable, scanForTree } = await loadTree();

    markNotHarvestable(OAK);

    expect(scanForTree().tree).toBeUndefined();
  });

  // The ban is learned on the shard and costs a walk and a swing to learn, so it goes into the
  // store that outlives the run rather than back into the config's seed
  it('survives a restart of the script', async () => {
    const { markNotHarvestable } = await loadTree();
    markNotHarvestable(OAK);

    vi.resetModules();
    vi.doMock('./config.js', async () => ({
      ...(await vi.importActual<object>('./config.js')),
      BOUNDS: undefined,
    }));
    const { isTree } = await import('./tree.js');

    expect(isTree(OAK)).toBe(false);
  });

  it('says so once and stays quiet on a repeat', async () => {
    const { markNotHarvestable } = await loadTree();

    markNotHarvestable(OAK);
    markNotHarvestable(OAK);

    expect(world.log).toHaveBeenCalledTimes(1);
  });

  it('leaves other arts alone', async () => {
    world.client.getStatic.mockReturnValue({ name: 'oak tree' });
    const { isTree, markNotHarvestable } = await loadTree();

    markNotHarvestable(OAK);

    expect(isTree(0x0ce1)).toBe(true);
  });
});

describe('scanForTree', () => {
  it('finds nothing in empty terrain', async () => {
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree).toBeUndefined();
  });

  it('finds a tree and reports its distance', async () => {
    world.client.getTerrainList = terrainFrom([tile({ x: 103, y: 100, graphic: OAK })]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree).toMatchObject({ x: 103, y: 100, graphic: OAK, distance: 3 });
  });

  it('prefers the nearer of two trees', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 108, y: 100, graphic: OAK }),
      tile({ x: 102, y: 100, graphic: OAK }),
    ]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree?.x).toBe(102);
  });

  // Chebyshev, because that is how the shard measures range: a diagonal step covers both axes, so
  // (103,103) is 3 away and not 6 - and closer than (105,100)
  it('measures distance the way the shard does', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 103, y: 103, graphic: OAK }),
      tile({ x: 105, y: 100, graphic: OAK }),
    ]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree).toMatchObject({ x: 103, y: 103, distance: 3 });
  });

  // target.terrain on a land tile is answered as mining rather than chopping
  it('ignores land tiles even when their graphic reads as a tree', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 101, y: 100, graphic: OAK, isLand: true }),
      tile({ x: 105, y: 100, graphic: OAK }),
    ]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree?.x).toBe(105);
  });

  it('ignores statics that are not trees', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 101, y: 100, graphic: ROCK }),
      tile({ x: 105, y: 100, graphic: OAK }),
    ]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree?.x).toBe(105);
  });

  it('trusts the tile its own coordinates rather than the ones it scanned with', async () => {
    world.client.getTerrainList = vi.fn((x: number, y: number) =>
      x === 101 && y === 100 ? [tile({ x: 95, y: 96, z: 7, graphic: OAK })] : [],
    );
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree).toMatchObject({ x: 95, y: 96, z: 7 });
  });

  it('finds nothing beyond the roam radius', async () => {
    world.client.getTerrainList = terrainFrom([tile({ x: 500, y: 500, graphic: OAK })]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree).toBeUndefined();
  });

  // A stand chopped to stumps used to leave the character standing in it for REGROW_DELAY. The wide
  // sweep is what walks it to the next stand instead.
  it('widens past the scan radius once the near box is dry', async () => {
    world.client.getTerrainList = terrainFrom([tile({ x: 118, y: 100, graphic: OAK })]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree?.x).toBe(118);
  });

  it('spends the wide sweep only when the near box has nothing', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 105, y: 100, graphic: OAK }),
      tile({ x: 118, y: 100, graphic: OAK }),
    ]);
    const { scanForTree } = await loadTree();

    expect(scanForTree().tree?.x).toBe(105);
  });

  // The reported bug: trees are the impassable statics the walk has to cross, so the nearest one was
  // picked, shuffled at, and written off for five minutes - over and over, until the box was empty
  it('drops a tree there is no route to rather than picking it', async () => {
    world.client.getTerrainList = vi.fn((x: number, y: number) => {
      if (x === 105 && y === 100) {
        return [tile({ x, y, graphic: OAK })];
      }

      return [tile({ x, y, graphic: 3, isLand: true, flags: x === 103 ? IMPASSABLE : 0 })];
    });
    const { scanForTree } = await loadTree();

    expect(scanForTree()).toEqual({ tree: undefined, regrowsAt: undefined });
  });

  it('names what is holding it back when both sweeps come up empty', async () => {
    world.client.getTerrainList = terrainFrom([
      tile({ x: 102, y: 100, graphic: OAK }),
      tile({ x: 106, y: 100, graphic: OAK }),
    ]);
    const { markDepleted, markUnusable, scanForTree } = await loadTree();

    markDepleted(scanForTree().tree!);
    markUnusable(scanForTree().tree!, 'is not in line of sight');
    world.log.mockClear();

    scanForTree();

    expect(world.log).toHaveBeenCalledWith(
      `tree: nothing choppable within ${ROAM_RADIUS} - 1 regrowing, 1 written off for good, ` +
        '0 with no route',
    );
  });

  describe('depleted tiles', () => {
    it('stops returning a tile once it has run out of wood', async () => {
      world.client.getTerrainList = terrainFrom([
        tile({ x: 102, y: 100, graphic: OAK }),
        tile({ x: 106, y: 100, graphic: OAK }),
      ]);
      const { markDepleted, scanForTree } = await loadTree();

      const first = scanForTree().tree!;
      expect(first.x).toBe(102);

      markDepleted(first);

      expect(scanForTree().tree?.x).toBe(106);
    });

    // The reason the cooldown exists at all: a stump regrows, and a clearing worked out by lunchtime
    // is a forest again by the afternoon. Written off permanently, the run runs out of trees instead.
    it('offers the tile again once it has regrown', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markDepleted, scanForTree } = await loadTree();

      markDepleted(scanForTree().tree!);
      expect(scanForTree().tree).toBeUndefined();

      vi.setSystemTime(START + REGROW_DELAY + 1);

      expect(scanForTree().tree?.x).toBe(102);
    });

    it('keeps it back until the cooldown is actually up', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markDepleted, scanForTree } = await loadTree();

      markDepleted(scanForTree().tree!);

      vi.setSystemTime(START + REGROW_DELAY - 1000);

      expect(scanForTree().tree).toBeUndefined();
    });

    // What the loop waits on. Reported only when there is nothing to chop right now, and only for a
    // tile that is genuinely coming back.
    it('reports when the soonest cooling tile is due back', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markDepleted, scanForTree } = await loadTree();

      markDepleted(scanForTree().tree!);

      expect(scanForTree().regrowsAt).toBe(START + REGROW_DELAY);
    });

    it('reports the soonest of several, not the last one it happened to see', async () => {
      world.client.getTerrainList = terrainFrom([
        tile({ x: 102, y: 100, graphic: OAK }),
        tile({ x: 106, y: 100, graphic: OAK }),
      ]);
      const { markDepleted, scanForTree } = await loadTree();

      markDepleted({ x: 106, y: 100, z: 0, graphic: OAK });

      vi.setSystemTime(START + 60_000);
      markDepleted({ x: 102, y: 100, z: 0, graphic: OAK });

      expect(scanForTree().regrowsAt).toBe(START + REGROW_DELAY);
    });

    it('has nothing to report while there is still a tree to chop', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { scanForTree } = await loadTree();

      expect(scanForTree().regrowsAt).toBeUndefined();
    });

    // One tree is several statics and only the trunk is harvestable, so the foliage has to drop out
    // one static at a time rather than taking the whole x/y with it
    it('drops one static without dropping its neighbours at the same spot', async () => {
      world.client.getTerrainList = terrainFrom([
        tile({ x: 102, y: 100, z: 0, graphic: OAK }),
        tile({ x: 102, y: 100, z: 10, graphic: 0x0ce1 }),
      ]);
      world.client.getStatic.mockReturnValue({ name: 'oak tree' });
      const { markDepleted, scanForTree } = await loadTree();

      markDepleted({ x: 102, y: 100, z: 0, graphic: OAK });

      expect(scanForTree().tree).toMatchObject({ x: 102, y: 100, z: 10, graphic: 0x0ce1 });
    });

    // 25 minutes outlasts most runs, so a restart that forgot would swing at everything it had just
    // emptied. The store is on globalThis for exactly this.
    it('stays depleted across a restart of the script', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const first = await loadTree();
      first.markDepleted(first.scanForTree().tree!);

      vi.resetModules();
      vi.doMock('./config.js', async () => ({
        ...(await vi.importActual<object>('./config.js')),
        BOUNDS: undefined,
      }));
      const { scanForTree } = await import('./tree.js');

      expect(scanForTree().tree).toBeUndefined();
    });
  });

  describe('written-off tiles', () => {
    // Line of sight and scenery: no amount of waiting makes either of them choppable
    it('never offers a tile marked unusable again', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markUnusable, scanForTree } = await loadTree();

      markUnusable(scanForTree().tree!, 'is not in line of sight');

      vi.setSystemTime(START + 24 * 60 * 60 * 1000);

      expect(scanForTree().tree).toBeUndefined();
    });

    // Or the loop would sit and wait for a tile that is never coming back
    it('is not something the loop is told to wait for', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markUnusable, scanForTree } = await loadTree();

      markUnusable(scanForTree().tree!, 'is not in line of sight');

      expect(scanForTree().regrowsAt).toBeUndefined();
    });

    // Timed rather than permanent: what blocked the path is usually a player or a pet, and this
    // write-off now outlives the run that made it
    it('retries a tile the walk could not close on', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markUnreachable, scanForTree } = await loadTree();

      markUnreachable(scanForTree().tree!);
      expect(scanForTree().tree).toBeUndefined();

      vi.setSystemTime(START + UNREACHABLE_DELAY + 1);

      expect(scanForTree().tree?.x).toBe(102);
    });

    it('gives up entirely once every candidate is spoken for', async () => {
      world.client.getTerrainList = terrainFrom([tile({ x: 102, y: 100, graphic: OAK })]);
      const { markUnusable, scanForTree } = await loadTree();

      markUnusable(scanForTree().tree!, 'is not harvestable');

      expect(scanForTree()).toEqual({ tree: undefined, regrowsAt: undefined });
    });
  });
});
