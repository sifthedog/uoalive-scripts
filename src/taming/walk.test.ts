import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, mobile, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

const loadWalk = async () => import('./walk.js');

// The animal is wherever `at` says it is now, so a test can move it between steps the way the shard
// does
const animal = (at: () => { x: number; y: number }) => {
  world.client.findObject.mockImplementation(() =>
    mobile({ serial: 0x1234, graphic: 0x00d0, ...at() }),
  );
};

// The fixture's player.run does not move anybody, which is what a wall looks like from in here
const walks = () => {
  world.player.run = vi.fn(() => {
    world.player.x += 1;
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('walkTo', () => {
  it('says closed when it is already next to the animal', async () => {
    animal(() => ({ x: 101, y: 100 }));
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('closed');
    expect(world.player.run).not.toHaveBeenCalled();
  });

  // TAME_APPROACH is nearer than TAME_RANGE on purpose: stopping at the range the loop tests against
  // leaves one step by the animal enough to break it again
  it('closes past the range the loop walks at', async () => {
    animal(() => ({ x: 102, y: 100 }));
    walks();
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('closed');

    // At the old range this was already close enough, and it never took a step
    expect(world.player.run).toHaveBeenCalled();
  });

  it('says stuck when nothing it does moves it', async () => {
    animal(() => ({ x: 110, y: 100 }));
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('stuck');
  });

  // The one that keeps the chase alive: never caught, but the gap is smaller than it was
  it('says gained when the animal outran it but the gap closed', async () => {
    let x = 200;

    animal(() => ({ x: (x += 1), y: 100 }));
    walks();
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('gained');
  });

  it('says stuck when the animal is outrunning it outright', async () => {
    let x = 200;

    animal(() => ({ x: (x += 3), y: 100 }));
    walks();
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('stuck');
  });

  it('says stuck when the animal stops resolving mid-chase', async () => {
    world.client.findObject.mockReturnValue(undefined);
    const { walkTo } = await loadWalk();

    expect(walkTo(0x1234)).toBe('stuck');
  });
});

describe('keepUp', () => {
  it('takes a step when the animal has drifted out of range', async () => {
    animal(() => ({ x: 104, y: 100 }));
    const { keepUp } = await loadWalk();

    keepUp(0x1234);

    expect(world.player.run).toHaveBeenCalled();
  });

  it('stays where it is while the animal is still in reach', async () => {
    animal(() => ({ x: 102, y: 100 }));
    const { keepUp } = await loadWalk();

    keepUp(0x1234);

    expect(world.player.run).not.toHaveBeenCalled();
  });

  it('does nothing about an animal that no longer resolves', async () => {
    world.client.findObject.mockReturnValue(undefined);
    const { keepUp } = await loadWalk();

    keepUp(0x1234);

    expect(world.player.run).not.toHaveBeenCalled();
  });
});
