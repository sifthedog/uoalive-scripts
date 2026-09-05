import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

const loadGuards = async () => import('./guards.js');

beforeEach(() => {
  world = installGlobals();
});

describe('stopReason', () => {
  it('says nothing about a character with room for another pet', async () => {
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });

  it('stops the run when the follower slots are full', async () => {
    world.player.followers = 5;
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBe('no follower slots left');
  });

  // The client has not been told yet, and 0 >= 0 would end every run on its first cycle
  it('does not read an unreported maximum as no room', async () => {
    world.player.followers = 0;
    world.player.maxFollowers = 0;
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeUndefined();
  });

  it('still stops for the things it always stopped for', async () => {
    world.player.isDead = true;
    const { stopReason } = await loadGuards();

    expect(stopReason()).toBeTruthy();
  });
});
