import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import {
  DIFFERENT_ORE_TEXT,
  MAX_COMBINE_ATTEMPTS,
  ORE_GRAPHICS,
  ORE_SETTLE_POLL,
  ORE_SETTLE_TIMEOUT,
  THROTTLED_TEXT,
} from './config.js';
import { orePiles, oreTotal, waitForOre } from './ore.js';

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

describe('orePiles', () => {
  it('finds nothing in an empty pack', () => {
    expect(orePiles()).toEqual([]);
  });

  // The graphic only says how the pile is drawn, so every stack size is one candidate list
  it('collects piles of every stack size, largest first', () => {
    installGlobals({
      backpack: [
        ore(1, IRON, 1, ONE),
        ore(2, IRON, 9, TWO),
        ore(3, IRON, 3, THREE),
        ore(4, IRON, 2, MANY),
      ],
    });

    expect(orePiles().map((i) => i.serial)).toEqual([2, 3, 4, 1]);
  });

  it('ignores everything that is not ore', () => {
    installGlobals({ backpack: [ore(1, IRON, 5), item({ serial: 2, graphic: 0x0f3f })] });

    expect(orePiles().map((i) => i.serial)).toEqual([1]);
  });

  // Top level only, because the combine and the smelt both act by serial on loose piles. The
  // weight the loop steers by is oreTotal's business, and that one does recurse.
  it('does not look inside sub-containers', () => {
    installGlobals({
      backpack: [item({ serial: 1, graphic: 0x0e76, contents: [ore(2, IRON, 5)] })],
    });

    expect(orePiles()).toEqual([]);
  });
});

// The seeded graphics come from a stack-size table this shard has been caught disagreeing with, so
// the tooltip name is the way back - and one is enough, because the art joins the set. Which is why
// every test here gets its own module: a learned art lands in the config's own Set, so one test
// teaching it 0x1234 would have the next test's 'not ore' fixture come back as ore.
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

// A shard stands behind these: it merges the pairs `allows` accepts, and refuses the rest in the
// wording DIFFERENT_ORE_TEXT knows. The module remembers what it learns for the run, so every test
// gets its own copy of it.
const onShard = async (
  piles: Item[],
  allows: (primary: Item, dup: Item) => boolean = () => true,
  refusal: string = DIFFERENT_ORE_TEXT[0],
) => {
  vi.resetModules();

  const world = installGlobals();
  const pack = [...piles];
  let said = '';

  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents: pack }),
  });

  let held: Item | undefined;
  world.player.use.mockImplementation((serial: number) => {
    held = pack.find((pile) => pile.serial === serial);
  });

  world.target.waitTargetEntity.mockImplementation((serial: number) => {
    const primary = pack.find((pile) => pile.serial === serial);
    said = '';

    if (!held || !primary) {
      return true;
    }

    if (allows(primary, held)) {
      primary.amount = (primary.amount ?? 1) + (held.amount ?? 1);
      pack.splice(pack.indexOf(held), 1);
    } else {
      said = refusal;
    }

    return true;
  });

  world.journal.containsText.mockImplementation((text: string) => said.includes(text));

  const { groupOres } = await import('./ore.js');
  groupOres();

  return { world, pack };
};

const sameHue = (a: Item, b: Item) => (a.hue ?? 0) === (b.hue ?? 0);

describe('groupOres', () => {
  it('does nothing when there is no ore', async () => {
    const { world } = await onShard([]);

    expect(world.player.use).not.toHaveBeenCalled();
  });

  // One attempt is the price of not trusting hue: it is 0 for iron and for a pile the client has said
  // nothing about, so the shard has to be the one that says these two are different metals.
  it('spends one attempt finding out two lone piles are different metals', async () => {
    const { world, pack } = await onShard([ore(1, IRON, 5), ore(2, COPPER, 5)], sameHue);

    expect(world.player.use).toHaveBeenCalledTimes(1);
    expect(pack).toHaveLength(2);
  });

  // Double-click one pile and target another, which is what works by hand on this shard. The
  // largest is the target so the smaller pile is the one consumed.
  it('combines a smaller pile into the largest one of its metal', async () => {
    const { world, pack } = await onShard([ore(1, IRON, 3), ore(2, IRON, 30)]);

    expect(world.player.use).toHaveBeenCalledWith(1);
    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(2, expect.any(Number));
    expect(pack.map((pile) => pile.amount)).toEqual([33]);
  });

  it('works a pile of three down to one', async () => {
    const { pack } = await onShard([ore(1, IRON, 3), ore(2, IRON, 30), ore(3, IRON, 7)]);

    expect(pack.map((pile) => pile.amount)).toEqual([40]);
  });

  // The bug this grouping exists to fix: hue reads 0 for a pile the client has not been sent the
  // properties of, so two piles of one metal can arrive wearing different hues.
  it('merges two piles the shard accepts even when their hues disagree', async () => {
    const { pack } = await onShard([ore(1, IRON, 30), ore(2, COPPER, 3)]);

    expect(pack.map((pile) => pile.amount)).toEqual([33]);
  });

  it('leaves two metals the shard refuses apart', async () => {
    const { pack } = await onShard([ore(1, IRON, 30), ore(2, COPPER, 3)], sameHue);

    expect(pack.map((pile) => pile.serial)).toEqual([1, 2]);
  });

  it('does not offer a refused pair a second time', async () => {
    const { world } = await onShard(
      [ore(1, IRON, 30), ore(2, COPPER, 3), ore(3, COPPER, 2)],
      sameHue,
    );

    expect(world.player.use.mock.calls.filter(([serial]) => serial === 2)).toHaveLength(1);
  });

  // Nothing was attempted, so nothing has been learned - the pair is still worth trying
  it('holds a throttled attempt against nobody', async () => {
    const { world } = await onShard([ore(1, IRON, 30), ore(2, IRON, 3)], () => false, THROTTLED_TEXT[0]);

    expect(world.player.use.mock.calls.length).toBeGreaterThan(1);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('says wait'));
  });

  it('reports a missing target cursor and cancels it', async () => {
    vi.resetModules();
    const world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30)] });
    world.target.waitTargetEntity.mockReturnValue(false);

    const { groupOres } = await import('./ore.js');
    groupOres();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('no target cursor'));
    expect(world.target.cancel).toHaveBeenCalled();
  });

  // A shard that answers a combine with silence, which is also what a pack the client has not
  // refreshed looks like. It must not loop, and it must say what it left behind.
  it('gives up on a silent pair and names what is left', async () => {
    vi.resetModules();
    const world = installGlobals({ backpack: [ore(1, IRON, 3), ore(2, IRON, 30)] });

    const { groupOres } = await import('./ore.js');
    groupOres();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('nothing was said'));
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('left 2 piles'));
  });

  it('stops at the attempt backstop rather than looping', async () => {
    vi.resetModules();
    const world = installGlobals({
      backpack: [ore(1, IRON, 3), ore(2, IRON, 30)],
    });
    world.journal.containsText.mockImplementation((text: string) =>
      THROTTLED_TEXT[0].includes(text),
    );

    const { groupOres } = await import('./ore.js');
    groupOres();

    expect(world.player.use).toHaveBeenCalledTimes(MAX_COMBINE_ATTEMPTS);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('backstop'));
  });
});

// The wait the loop takes before grouping. A pack that arrives late is the reason it exists; one
// that never changes is the reason it is bounded.
describe('waitForOre', () => {
  // The common case, and the one worth keeping cheap: the ore is usually already there by the time
  // the journal line announcing it has been read, so this must not cost a poll interval per swing.
  it('returns at once when the ore has already landed, without sleeping', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 33)] });

    expect(waitForOre(0)).toBe(true);
    expect(world.sleep).not.toHaveBeenCalled();
  });

  it('waits for a pile that arrives a poll or two later', () => {
    const packs = [[ore(1, IRON, 30)], [ore(1, IRON, 30), ore(2, IRON, 3)]];
    let arrived = 0;

    world = installGlobals();
    Object.defineProperty(world.player, 'backpack', {
      configurable: true,
      get: () => ({ serial: 0x40000000, contents: packs[Math.min(arrived, 1)] }),
    });
    world.sleep.mockImplementation(() => {
      arrived++;
    });

    expect(waitForOre(30)).toBe(true);
    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  // A swing read as 'dug' whose ore never turns up. Grouping still happens - the caller ignores this
  // - so the only thing that matters is that it stops asking.
  it('gives up at the timeout when nothing arrives', () => {
    world = installGlobals({ backpack: [ore(1, IRON, 30)] });

    expect(waitForOre(30)).toBe(false);
    expect(world.sleep).toHaveBeenCalledTimes(ORE_SETTLE_TIMEOUT / ORE_SETTLE_POLL);
  });

  // Hue-blind and pile-blind both: what is being waited for is ore in the pack, whatever colour it
  // came out as and whether the shard delivered it loose or merged into the pile already there.
  it('is satisfied by ore that merged into an existing pile', () => {
    world = installGlobals({ backpack: [ore(1, COPPER, 31)] });

    expect(waitForOre(30)).toBe(true);
    expect(world.sleep).not.toHaveBeenCalled();
  });
});
