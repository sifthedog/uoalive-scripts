import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { ORE_GRAPHICS } from './config.js';
import { groupOres, oreTotal, oresByHue } from './ore.js';

const IRON = 0;
const COPPER = 0x60c;

// The stock tables call these the 1, 2, 3 and 4+ sizes, which this shard does not honour - a pile
// of 33 wears the first of them. Kept as names because the fixtures read better with them.
const [ONE, TWO, THREE, MANY] = [...ORE_GRAPHICS];

let world: FakeWorld;

const ore = (serial: number, hue: number, amount: number, graphic = MANY) =>
  item({ serial, graphic, hue, amount });

beforeEach(() => {
  world = installGlobals();
});

describe('oresByHue', () => {
  it('finds nothing in an empty pack', () => {
    expect(oresByHue().size).toBe(0);
  });

  // Ore is grouped by hue and never by graphic, because the graphic only says how big the pile is
  it('groups piles of every stack size together', () => {
    installGlobals({
      backpack: [
        ore(1, IRON, 1, ONE),
        ore(2, IRON, 2, TWO),
        ore(3, IRON, 3, THREE),
        ore(4, IRON, 9, MANY),
      ],
    });

    expect(oresByHue().get(IRON)?.map((i) => i.serial)).toEqual([1, 2, 3, 4]);
  });

  it('keeps two ore types apart', () => {
    installGlobals({ backpack: [ore(1, IRON, 5), ore(2, COPPER, 5), ore(3, IRON, 5)] });

    const groups = oresByHue();

    expect(groups.get(IRON)?.map((i) => i.serial)).toEqual([1, 3]);
    expect(groups.get(COPPER)?.map((i) => i.serial)).toEqual([2]);
  });

  it('treats a missing hue as iron', () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: MANY, amount: 5 })] });

    expect(oresByHue().get(IRON)).toHaveLength(1);
  });

  it('ignores everything that is not ore', () => {
    installGlobals({ backpack: [ore(1, IRON, 5), item({ serial: 2, graphic: 0x0f3f })] });

    expect(oresByHue().get(IRON)).toHaveLength(1);
  });

  // Top level only, because the combine and the smelt both act by serial on loose piles. The
  // weight the loop steers by is oreTotal's business, and that one does recurse.
  it('does not look inside sub-containers', () => {
    installGlobals({
      backpack: [item({ serial: 1, graphic: 0x0e76, contents: [ore(2, IRON, 5)] })],
    });

    expect(oresByHue().size).toBe(0);
  });
});

// The seeded graphics come from a stack-size table this shard has already been caught disagreeing
// with, so an art the set has never heard of is not a remote possibility. The tooltip name is the
// way back from that, and one is enough: the art joins the set.
//
// Which is why every test here gets its own copy of the module. A learned art lands in the config's
// own Set - deliberately, the way boards.ts learns a board graphic - so one test teaching it 0x1234
// would otherwise have the next test's 'not ore' fixture come back as ore.
describe('isOrePile', () => {
  const loadOre = async () => import('./ore.js');

  beforeEach(() => {
    vi.resetModules();
  });

  it('matches by graphic without needing a name', async () => {
    const { isOrePile } = await loadOre();

    expect(isOrePile(item({ serial: 1, graphic: MANY }))).toBe(true);
  });

  it('matches an unknown art by its name', async () => {
    const { isOrePile } = await loadOre();

    expect(isOrePile(item({ serial: 1, graphic: 0x1234, name: '33 Ore' }))).toBe(true);
  });

  it('remembers that art, so the next one costs no tooltip', async () => {
    const { isOrePile } = await loadOre();

    isOrePile(item({ serial: 1, graphic: 0x1234, name: '33 Ore' }));

    expect(isOrePile(item({ serial: 2, graphic: 0x1234, name: '' }))).toBe(true);
  });

  // A whole word, on the precedent of the key search in src/boxes: 'ore' at the end of 'sycamore'
  // would put something in the smelter that was never meant to go there
  it('does not match a name that merely contains those letters', async () => {
    const { isOrePile } = await loadOre();

    expect(isOrePile(item({ serial: 1, graphic: 0x1234, name: 'a sycamore board' }))).toBe(false);
  });

  it('rejects an item that is neither a known art nor named ore', async () => {
    const { isOrePile } = await loadOre();

    expect(isOrePile(item({ serial: 1, graphic: 0x1234, name: 'iron ingot' }))).toBe(false);
  });

  it('says so when it learns one, so a wrong match is visible', async () => {
    const { isOrePile } = await loadOre();

    isOrePile(item({ serial: 1, graphic: 0x1234, name: '33 Ore' }));

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('0x1234'));
  });
});

describe('oreTotal', () => {
  it('adds up the amounts rather than counting the piles', () => {
    installGlobals({ backpack: [ore(1, IRON, 30), ore(2, COPPER, 12)] });

    expect(oreTotal()).toBe(42);
  });

  // The counterpart to oresByHue's top-level rule: what the loop weighs itself against includes the
  // ore someone tidied into a bag, or the pack reads as empty while the character cannot move
  it('counts ore inside bags too', () => {
    installGlobals({
      backpack: [ore(1, IRON, 5), item({ serial: 9, graphic: 0x0e76, contents: [ore(2, IRON, 7)] })],
    });

    expect(oreTotal()).toBe(12);
  });

  it('treats a pile with no amount as one', () => {
    installGlobals({ backpack: [item({ serial: 1, graphic: MANY, hue: IRON })] });

    expect(oreTotal()).toBe(1);
  });

  it('ignores everything that is not ore', () => {
    installGlobals({ backpack: [ore(1, IRON, 5), item({ serial: 2, graphic: 0x0f3f, amount: 99 })] });

    expect(oreTotal()).toBe(5);
  });
});

describe('groupOres', () => {
  it('does nothing when there is no ore', () => {
    groupOres();

    expect(world.player.use).not.toHaveBeenCalled();
  });

  it('does nothing when each hue is already a single pile', () => {
    installGlobals({ backpack: [ore(1, IRON, 5), ore(2, COPPER, 5)] });

    groupOres();

    expect(world.player.use).not.toHaveBeenCalled();
  });

  // Double-click one pile and target another, which is what works by hand on this shard. The
  // largest is the target so the smaller pile is the one consumed.
  it('combines a smaller pile into the largest one of its hue', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30)] });

    groupOres();

    expect(world.player.use).toHaveBeenCalledWith(1);
    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(2, expect.any(Number));
  });

  it('leaves a lone pile of another hue untouched', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30), ore(3, COPPER, 5)] });

    groupOres();

    expect(world.player.use).not.toHaveBeenCalledWith(3);
  });

  // A combine consumes one of the two piles, so the pack is rescanned between passes rather than
  // planned up front. With a fake pack that never changes, that is a stall - and it must not loop.
  it('bails out rather than looping when a pass makes no progress', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30)] });

    groupOres();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('stalled'));
  });

  it('reports a missing target cursor and cancels it', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30)] });
    world.target.waitTargetEntity.mockReturnValue(false);

    groupOres();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no target cursor'));
    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('stops once the piles have actually merged', () => {
    const packs = [
      [ore(1, IRON, 3), ore(2, IRON, 30)],
      [ore(2, IRON, 33)],
    ];
    let pass = 0;
    world = installGlobals();
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents: packs[Math.min(pass, 1)] }),
    });
    world.target.waitTargetEntity.mockImplementation(() => {
      pass = 1;
      return true;
    });

    groupOres();

    expect(world.log).not.toHaveBeenCalledWith(expect.stringContaining('stalled'));
    expect(world.player.use).toHaveBeenCalledTimes(1);
  });
});
