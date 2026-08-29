import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, terrainMap, tile, type FakeWorld } from '../test-support/uo.js';
import { BRIDGE, IMPASSABLE, SURFACE, WET } from './flags.js';
import { createGrid } from './grid.js';

let world: FakeWorld;

const OPTIONS = {
  radius: 16,
  maxSteps: 40,
  maxNodes: 1500,
  maxCells: 20_000,
  climb: 2,
  height: 16,
  headroom: 2,
};

const grid = (overrides: Partial<Parameters<typeof createGrid>[0]> = {}) =>
  createGrid({ ...OPTIONS, ...overrides });

// The character stands at the map's origin, so a picture reads as what is around them
const AT: [number, number] = [0, 0];

// A picture with the character in the middle, walked with a flood no wider than the picture - so
// what is drawn is the whole world and a route cannot slip out through the unknown around it
const BOX: [number, number] = [-4, -4];
const walled = () => grid({ radius: 4 });
const rows = (row: string) => Array<string>(9).fill(row);

beforeEach(() => {
  world = installGlobals({ player: { x: 0, y: 0 } });
});

describe('what can be stood on', () => {
  // Asked about a tile two east, with plain ground everywhere else, so the answer is about the tile
  // rather than about the square the character is standing on
  const standing = (entries: ReturnType<typeof tile>[], groundZ = 0): boolean => {
    world.player.z = groundZ;
    world.client.getTerrainList = vi.fn((x: number, y: number) =>
      x === 2 && y === 0 ? entries : [tile({ x, y, z: groundZ, graphic: 3, isLand: true })],
    );

    return grid().stepsTo({ x: 2, y: 0 }, 0) !== undefined;
  };

  it('stands on plain land', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 3, isLand: true })])).toBe(true);
  });

  it('does not stand on impassable land, which is what a mountain face is', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 231, isLand: true, flags: IMPASSABLE })])).toBe(
      false,
    );
  });

  // Passable by the flags, and still not somewhere a character on foot ends up
  it('does not stand in water', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 168, isLand: true, flags: WET })])).toBe(false);
  });

  // Land is a surface by definition and never sets the bit, so the two kinds have to be asked
  // different questions
  it('stands on a static that carries the surface flag', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 1339, flags: SURFACE })])).toBe(true);
  });

  it('stands on a bridge, which is how stairs and ramps are marked', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 1339, flags: BRIDGE })])).toBe(true);
  });

  it('does not stand on a static that is neither a surface nor a bridge', () => {
    expect(standing([tile({ x: 2, y: 0, graphic: 0x0b4e })])).toBe(false);
  });

  it('refuses a floor with something solid standing on it', () => {
    const floor = tile({ x: 2, y: 0, graphic: 3, isLand: true });
    const wall = tile({ x: 2, y: 0, graphic: 0x0006, flags: IMPASSABLE });

    expect(standing([floor, wall])).toBe(false);
  });

  it('keeps a floor under a roof, which is solid and far enough above to walk beneath', () => {
    const floor = tile({ x: 2, y: 0, graphic: 3, isLand: true });
    const roof = tile({ x: 2, y: 0, z: 20, graphic: 0x0006, flags: IMPASSABLE });

    expect(standing([floor, roof])).toBe(true);
  });

  // The whole of the no-height approximation: a wall based just under the floor still blocks it
  it('refuses a floor with something solid based just below it', () => {
    const floor = tile({ x: 2, y: 0, graphic: 3, isLand: true });
    const wall = tile({ x: 2, y: 0, z: -1, graphic: 0x0006, flags: IMPASSABLE });

    expect(standing([floor, wall])).toBe(false);
  });

  it('keeps a bridge over a chasm, where the impassable land is far below it', () => {
    const chasm = tile({ x: 2, y: 0, graphic: 231, isLand: true, flags: IMPASSABLE });
    const bridge = tile({ x: 2, y: 0, z: 20, graphic: 1339, flags: SURFACE });

    expect(standing([chasm, bridge], 20)).toBe(true);
  });
});

// Every map coordinate has a land tile, so an empty answer means the chunk is not loaded. Refusing
// to walk on missing information is how a filter meant to stop bad walks starts stopping good ones.
describe('terrain the client cannot answer for', () => {
  it('walks through it rather than refusing it', () => {
    world.client.getTerrainList = vi.fn(() => []);

    expect(grid().stepsTo({ x: 10, y: 0 }, 0)).toBe(10);
  });

  it('does not remember it, so a chunk that loads later is seen', () => {
    let loaded = false;

    world.client.getTerrainList = vi.fn((x: number, y: number) =>
      loaded && x === 2 ? [tile({ x, y, graphic: 231, isLand: true, flags: IMPASSABLE })] : [],
    );

    const walkable = grid();

    expect(walkable.stepsTo({ x: 4, y: 0 }, 0)).toBe(4);

    loaded = true;
    world.player.x = 1;

    expect(walkable.stepsTo({ x: 4, y: 0 }, 0)).toBeUndefined();
  });

  it('remembers terrain it did get, so a coordinate is read once', () => {
    world.client.getTerrainList = terrainMap(AT, ['.....', '.....', '.....']);
    const walkable = grid();

    walkable.stepsTo({ x: 2, y: 0 }, 0);
    world.player.x = 1;
    walkable.stepsTo({ x: 2, y: 0 }, 0);

    const asked = world.client.getTerrainList.mock.calls.filter(
      (call) => call[0] === 2 && call[1] === 0,
    );

    expect(asked).toHaveLength(1);
  });
});

describe('routes', () => {
  // The reported bug: a wall of ore where every tile is nearest by straight-line distance and none
  // of them can be walked to, so the run wrote the face off one tile and one cooldown at a time
  const WALL = rows('.....#...');

  it('refuses a vein walled off from the character', () => {
    world.client.getTerrainList = terrainMap(BOX, WALL);

    expect(walled().stepsTo({ x: 3, y: 0 }, 0)).toBeUndefined();
  });

  // The straight line is three steps, so anything longer is the detour being taken
  it('finds the way through a gap in the same wall, the long way round', () => {
    world.client.getTerrainList = terrainMap(BOX, [...WALL.slice(0, 8), '.........']);

    expect(walled().stepsTo({ x: 3, y: 0 }, 0)).toBe(10);
  });

  // A vein is the mountain face itself, which is exactly what cannot be stood on - so the question
  // is whether anything within swinging range of it can be. Answer this wrong and mining finds
  // nothing anywhere.
  it('reaches the foot of a mountain, though the vein itself cannot be stood on', () => {
    world.client.getTerrainList = terrainMap(BOX, rows('.......##'));

    expect(walled().stepsTo({ x: 4, y: 0 }, 2)).toBe(2);
  });

  it('takes the straight line on open ground, so a corridor is walked straight down', () => {
    world.client.getTerrainList = terrainMap([-4, -4], Array(9).fill('.........'));

    expect(grid().routeTo({ x: 4, y: 0 }, 0)).toEqual([1, 0]);
    expect(grid().routeTo({ x: 4, y: 4 }, 0)).toEqual([1, 1]);
    expect(grid().routeTo({ x: 0, y: -4 }, 0)).toEqual([0, -1]);
    expect(grid().routeTo({ x: -4, y: 2 }, 0)).toEqual([-1, 1]);
  });

  it('steps around a wall rather than into it', () => {
    world.client.getTerrainList = terrainMap([0, -2], [
      '..#..',
      '..#..',
      '..#..',
      '.....',
    ]);

    expect(grid().routeTo({ x: 4, y: 0 }, 0)).toEqual([1, 1]);
  });

  it('has no route to offer when the goal is walled off', () => {
    world.client.getTerrainList = terrainMap(BOX, WALL);

    expect(walled().routeTo({ x: 3, y: 0 }, 0)).toBeUndefined();
  });

  it('offers no step when the character is already in range', () => {
    world.client.getTerrainList = terrainMap(AT, ['.....']);

    expect(grid().routeTo({ x: 2, y: 0 }, 2)).toBeUndefined();
  });
});

describe('the box a run is confined to', () => {
  const OPEN = rows('.........');

  // Lumberjacking passes its bounds box here: a route planned through ground outside it would be
  // refused a step at a time by allowedStep and the tree written off as unreachable
  const west = (x: number) => x <= 2;

  it('refuses a goal there is no legal spot beside', () => {
    world.client.getTerrainList = terrainMap(BOX, OPEN);

    expect(grid({ passable: west }).stepsTo({ x: 4, y: 0 }, 0)).toBeUndefined();
    expect(grid({ passable: west }).routeTo({ x: 4, y: 0 }, 0)).toBeUndefined();
  });

  it('will not plan the way round through ground outside it', () => {
    world.client.getTerrainList = terrainMap(BOX, [...rows('.....#...').slice(0, 8), '.........']);

    expect(grid({ radius: 4, passable: (_x, y) => y <= 3 }).stepsTo({ x: 3, y: 0 }, 0)).toBeUndefined();
  });

  it('is absent for a run that roams', () => {
    world.client.getTerrainList = terrainMap(BOX, OPEN);

    expect(grid().stepsTo({ x: 4, y: 0 }, 0)).toBe(4);
  });
});

describe('the climb rule', () => {
  it('steps up onto a ledge within the climb', () => {
    world.client.getTerrainList = terrainMap(AT, ['.x'], {
      '.': { isLand: true },
      x: { isLand: true, z: 2 },
    });

    expect(grid().stepsTo({ x: 1, y: 0 }, 0)).toBe(1);
  });

  it('will not step up onto one past it', () => {
    world.client.getTerrainList = terrainMap(AT, ['.x'], {
      '.': { isLand: true },
      x: { isLand: true, z: 3 },
    });

    expect(grid().stepsTo({ x: 1, y: 0 }, 0)).toBeUndefined();
  });

  // Symmetric on purpose: the route is flooded from the goal, walking its steps backwards, and an
  // asymmetric rule there plans a climb the character cannot make
  it('will not drop further than it would climb', () => {
    world.client.getTerrainList = terrainMap(AT, ['.x'], {
      '.': { isLand: true },
      x: { isLand: true, z: -3 },
    });

    expect(grid().stepsTo({ x: 1, y: 0 }, 0)).toBeUndefined();
  });
});

// The shard wants both sides of a diagonal open, and a route that assumes otherwise comes back a
// step short at every doorway
describe('diagonals', () => {
  const corner = (rows: string[]) => {
    world.client.getTerrainList = terrainMap([-1, -1], ['###', ...rows]);

    return grid({ radius: 1 }).stepsTo({ x: 1, y: 1 }, 0);
  };

  it('takes one with both of its sides open', () => {
    expect(corner(['#..', '#..'])).toBe(1);
  });

  // One side open is still not a diagonal - it is a way round, one step longer
  it('goes around one with a side blocked', () => {
    expect(corner(['#.#', '#..'])).toBe(2);
  });

  it('refuses one with both sides blocked', () => {
    expect(corner(['#.#', '##.'])).toBeUndefined();
  });
});

it('stops searching at the node cap rather than flooding an open world', () => {
  world.client.getTerrainList = vi.fn((x: number, y: number) => [
    tile({ x, y, graphic: 3, isLand: true }),
  ]);

  expect(grid({ maxNodes: 9 }).stepsTo({ x: 10, y: 0 }, 0)).toBeUndefined();
});

// The flag values are hand-written from the stock tables, so a shard that numbers them differently
// would have this file report an empty world and blame the shard for it
describe('when the flags are wrong for the shard', () => {
  beforeEach(() => {
    world.client.getTerrainList = vi.fn((x: number, y: number) => [
      tile({ x, y, graphic: 3, isLand: true, flags: IMPASSABLE }),
    ]);
  });

  it('says so, once', () => {
    const walkable = grid();

    walkable.stepsTo({ x: 2, y: 0 }, 0);
    world.player.x = 1;
    walkable.stepsTo({ x: 2, y: 0 }, 0);

    const said = world.log.mock.calls.filter((call) =>
      String(call[0]).includes('under your feet reads as impassable'),
    );

    expect(said).toHaveLength(1);
  });

  it('stops filtering, rather than reporting a world with nowhere to stand', () => {
    expect(grid().stepsTo({ x: 5, y: 0 }, 0)).toBe(5);
  });

  it('leaves the walk to step the way it always did', () => {
    expect(grid().routeTo({ x: 5, y: 0 }, 0)).toBeUndefined();
  });
});
