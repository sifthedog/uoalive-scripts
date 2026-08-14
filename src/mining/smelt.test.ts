import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, mobile, type FakeWorld } from '../test-support/uo.js';
import { ORE_GRAPHICS, SMELT_ATTEMPTS } from './config.js';

const BEETLE_BODY = 0xa9;
const BEETLE = 0x0000c001;
const INGOT = 0x1bf2;
const NEW_INGOT = 0x1bef;

// The stock tables call these the 1, 2, 3 and 4+ sizes. They are not that here - a pile of 33 wears
// the first one - so the names are kept only because the fixtures read better with them.
const [ONE, TWO, , MANY] = [...ORE_GRAPHICS];

const IRON = 0;
const VALORITE = 0x08a5;

let world: FakeWorld;

// smelt.ts latches the beetle's serial, whether it has reported one, and the hues it has given up
// on, so each test needs its own copy of the module
const loadSmelt = async () => import('./smelt.js');

const ore = (serial: number, hue: number, amount = 10, graphic = MANY) =>
  item({ serial, graphic, hue, amount });

const beetle = (extra: Partial<Mobile> = {}) =>
  mobile({ serial: BEETLE, graphic: BEETLE_BODY, name: 'Smelty', x: 100, y: 100, isRenamable: true, ...extra });

// The beetle is standing where you are unless a test says otherwise, so nothing has to walk
const beetleNearby = (found: Mobile[] = [beetle()]) => {
  world.client.findAllMobilesOfType.mockReturnValue(found);
  world.client.findObject.mockImplementation((serial: number) =>
    found.find((candidate) => candidate.serial === serial),
  );
};

// A smelt that lands: the pack swaps its ore for ingots the moment the beetle is targeted
const smeltWorks = (packs: Item[][], ingotGraphic = INGOT) => {
  let pass = 0;
  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({ serial: 0x40000000, contents: packs[Math.min(pass, packs.length - 1)] }),
  });
  world.target.waitTargetEntity.mockImplementation(() => {
    pass++;
    return true;
  });
  return ingotGraphic;
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('findBeetle', () => {
  it('finds one by its body graphic', async () => {
    beetleNearby();
    const { findBeetle } = await loadSmelt();

    expect(findBeetle()?.serial).toBe(BEETLE);
    expect(world.client.findAllMobilesOfType).toHaveBeenCalledWith(
      BEETLE_BODY,
      null,
      null,
      null,
      expect.any(Number),
    );
  });

  // Only your own pets can be renamed, so this is what tells yours from a stranger's
  it('prefers one that is yours over one that is not', async () => {
    beetleNearby([
      beetle({ serial: 0x0000c002, isRenamable: false, x: 100, y: 100 }),
      beetle({ serial: BEETLE, isRenamable: true, x: 104, y: 100 }),
    ]);
    const { findBeetle } = await loadSmelt();

    expect(findBeetle()?.serial).toBe(BEETLE);
  });

  it('takes the nearest when several are yours', async () => {
    beetleNearby([
      beetle({ serial: 0x0000c002, x: 106, y: 100 }),
      beetle({ serial: BEETLE, x: 101, y: 100 }),
    ]);
    const { findBeetle } = await loadSmelt();

    expect(findBeetle()?.serial).toBe(BEETLE);
  });

  it('finds nothing when there is nothing to find', async () => {
    const { findBeetle } = await loadSmelt();

    expect(findBeetle()).toBeUndefined();
  });

  // The body graphic is a guess at this shard, so the console has to name what it settled on
  it('names the beetle it settled on, once', async () => {
    beetleNearby();
    const { findBeetle } = await loadSmelt();

    findBeetle();
    findBeetle();

    const said = world.log.mock.calls.filter(([line]) => String(line).includes('as the forge'));
    expect(said).toHaveLength(1);
  });
});

describe('smeltAll', () => {
  it('does nothing at all when there is no ore', async () => {
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    expect(smeltAll()).toBe(true);
    expect(world.client.findAllMobilesOfType).not.toHaveBeenCalled();
  });

  it('uses the ore and targets the beetle, in that order', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    smeltWorks([[ore(1, IRON)], [item({ serial: 2, graphic: INGOT, hue: IRON, amount: 5 })]]);
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(1);
    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(BEETLE, expect.any(Number));
  });

  // A fire beetle is rideable, so a double-click mounts you - the exact thing mount.ts exists to
  // undo. It is only ever a target, never something this script uses.
  it('never double-clicks the beetle itself', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    smeltWorks([[ore(1, IRON)], [item({ serial: 2, graphic: INGOT, hue: IRON, amount: 5 })]]);
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).not.toHaveBeenCalledWith(BEETLE);
  });

  // The smelt is silent on stock RunUO, so the pack diff is the only evidence of it - and the diff
  // also names this shard's ingot graphic, whatever the art id turns out to be
  it('learns the ingot graphic from the pack diff', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    smeltWorks([[ore(1, IRON)], [item({ serial: 2, graphic: 0x1234, hue: IRON, amount: 5 })]]);
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('ingot graphic is 0x1234'));
  });

  it('says nothing about a graphic it already knew', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    smeltWorks([[ore(1, IRON)], [item({ serial: 2, graphic: NEW_INGOT, hue: IRON, amount: 5 })]]);
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.log).not.toHaveBeenCalledWith(expect.stringContaining('ingot graphic'));
  });

  // The shard saying it outright is worth acting on immediately: a coloured ore needs the Mining
  // skill to work it, and no amount of retrying supplies that
  it('gives up on a hue the shard says you cannot work', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, VALORITE)] });
    beetleNearby();
    world.journal.containsText.mockImplementation((text: string) =>
      text.includes('not skilled enough'),
    );
    const { smeltAll, unsmeltable } = await loadSmelt();

    smeltAll();

    expect(unsmeltable.has(VALORITE)).toBe(true);
    expect(world.player.use).toHaveBeenCalledTimes(1);
  });

  // Silence is also what a throttled or stale attempt looks like, so one is not enough to conclude
  // anything - but a hue that never lands has to leave the candidate set, or the loop runs to its
  // backstop instead of shrinking
  it('gives up on a hue only after it has stayed silent SMELT_ATTEMPTS times', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    const { smeltAll, unsmeltable } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledTimes(SMELT_ATTEMPTS);
    expect(unsmeltable.has(IRON)).toBe(true);
  });

  it('counts a missing target cursor as one of those failures', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    world.target.waitTargetEntity.mockReturnValue(false);
    const { smeltAll, unsmeltable } = await loadSmelt();

    smeltAll();

    expect(unsmeltable.has(IRON)).toBe(true);
    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('leaves an ore of another hue alone once it has given up on one', async () => {
    world = installGlobals({
      player: { x: 100, y: 100 },
      backpack: [ore(1, VALORITE), ore(2, IRON)],
    });
    beetleNearby();
    world.journal.containsText.mockImplementation((text: string) =>
      text.includes('not skilled enough'),
    );
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(2);
  });

  // Not fatal: the ore keeps, and a run that stopped over a wandering pet would be worse than one
  // that carries its ore home
  it('reports a missing beetle once and carries on', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    const { smeltAll } = await loadSmelt();

    expect(smeltAll()).toBe(false);
    smeltAll();

    const said = world.log.mock.calls.filter(([line]) => String(line).includes('no fire beetle'));
    expect(said).toHaveLength(1);
  });

  // The beetle is a pet and it wanders, so the smelt walks to it - and gives up on the pass rather
  // than the run if it cannot get there
  it('walks to a beetle that is out of range', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby([beetle({ x: 110, y: 100 })]);
    const { smeltAll } = await loadSmelt();

    expect(smeltAll()).toBe(false);
    expect(world.player.run).toHaveBeenCalled();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('cannot reach'));
  });

  it('finds ore that is sitting in a bag rather than loose', async () => {
    const bagged = item({ serial: 9, graphic: 0x0e76, contents: [ore(1, IRON)] });
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [bagged] });
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(1);
  });

  // Two ore make an ingot, so the shard refuses a lone one - silently, in a way the pack diff
  // cannot tell from a throttled attempt. Offered anyway it would burn three attempts and then
  // write off the whole hue, taking every future stack of iron with it.
  it('leaves a lone ore alone rather than failing three times over it', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON, 1, ONE)] });
    beetleNearby();
    const { smeltAll, unsmeltable } = await loadSmelt();

    expect(smeltAll()).toBe(true);
    expect(world.player.use).not.toHaveBeenCalled();
    expect(unsmeltable.has(IRON)).toBe(false);
  });

  // Skipped for its size, not remembered by hue: the next swing that lands on that vein makes it
  // two, and the stack has to be picked up again then
  it('smelts that same hue once there is more than one of it', async () => {
    world = installGlobals({
      player: { x: 100, y: 100 },
      backpack: [ore(1, IRON, 1, ONE), ore(2, IRON, 2, TWO)],
    });
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(2);
    expect(world.player.use).not.toHaveBeenCalledWith(1);
  });

  // Three silent passes is a thin basis for carrying a hue home: a beetle that wandered out of
  // range for a moment looks exactly the same. The loop asks for this rather than ending a run
  // overweight beside a working beetle and a pack full of ore.
  it('takes a hue back off the written-off list when asked', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    const { retryUnsmeltable, smeltAll, unsmeltable } = await loadSmelt();

    smeltAll();
    expect(unsmeltable.has(IRON)).toBe(true);

    expect(retryUnsmeltable()).toBe(true);
    expect(unsmeltable.has(IRON)).toBe(false);

    world.player.use.mockClear();
    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(1);
  });

  // Which is what stops the retry becoming a loop: the caller ends the run on the second false
  it('says there is nothing to reconsider when nothing was written off', async () => {
    const { retryUnsmeltable } = await loadSmelt();

    expect(retryUnsmeltable()).toBe(false);
  });

  // The misses are cleared along with the verdict, or the very next silent pass re-lands it
  it('gives the hue its full run of attempts again rather than one', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    const { retryUnsmeltable, smeltAll, unsmeltable } = await loadSmelt();

    smeltAll();
    retryUnsmeltable();
    world.player.use.mockClear();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledTimes(SMELT_ATTEMPTS);
    expect(unsmeltable.has(IRON)).toBe(true);
  });

  // item.amount is 0 for anything the client has no data for, and reading that as a pile of zero
  // skips every stack in the pack - a run that halts overweight beside a working beetle with ore it
  // could have smelted. An unknown size is worth one attempt; only a known one is skipped.
  it('tries a stack whose size the client has not told us', async () => {
    world = installGlobals({
      player: { x: 100, y: 100 },
      backpack: [item({ serial: 1, graphic: MANY, hue: IRON, amount: 0 })],
    });
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(1);
  });

  // The stock tables call this art a pile of one, and on this shard a pile of 33 wears it. Reading
  // a size off the graphic skips a full stack outright, so only the amount decides.
  it('smelts a full stack drawn with the art the tables call a single', async () => {
    world = installGlobals({
      player: { x: 100, y: 100 },
      backpack: [item({ serial: 1, graphic: ONE, hue: IRON, amount: 33 })],
    });
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.player.use).toHaveBeenCalledWith(1);
  });

  // 'smelting freed nothing' over a pack with ore in it is an accusation without evidence, and
  // every reason a pile is passed over is invisible from outside smelt.ts
  it('says what it is holding when none of it can be smelted', async () => {
    world = installGlobals({
      player: { x: 100, y: 100 },
      backpack: [ore(1, IRON, 1, ONE), ore(2, VALORITE, 30)],
    });
    beetleNearby();
    const { smeltAll, unsmeltable } = await loadSmelt();
    unsmeltable.add(VALORITE);

    smeltAll();

    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('too small'));
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('written off'));
  });

  // A frozen shard answers a smelt exactly the way an unworkable ore does - with nothing at all -
  // so without this a world save costs three attempts and writes the hue off for the rest of the run
  it('leaves the ore alone while the world is saving', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON)] });
    beetleNearby();
    world.journal.containsText.mockImplementation((text: string) =>
      text.includes('world is saving'),
    );
    const { smeltAll, unsmeltable } = await loadSmelt();

    expect(smeltAll()).toBe(false);
    expect(world.player.use).not.toHaveBeenCalled();
    expect(unsmeltable.has(IRON)).toBe(false);
  });

  it('stays quiet about an empty pack, which explains itself', async () => {
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.log).not.toHaveBeenCalled();
  });

  it('does not go looking for a beetle when the only ore is too small to smelt', async () => {
    world = installGlobals({ player: { x: 100, y: 100 }, backpack: [ore(1, IRON, 1, ONE)] });
    beetleNearby();
    const { smeltAll } = await loadSmelt();

    smeltAll();

    expect(world.client.findAllMobilesOfType).not.toHaveBeenCalled();
  });
});
