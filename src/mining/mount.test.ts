import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { DISMOUNT_ATTEMPTS } from './config.js';

const PLAYER = 0x0001d4a6;

let world: FakeWorld;

// mount.ts latches whether it has already said it is getting off, so each test needs a fresh copy
const loadMount = async () => import('./mount.js');

// A dismount that lands: the mount layer clears once the player is double-clicked
const dismountWorks = () => {
  world.player.use.mockImplementation((serial: number) => {
    if (serial === PLAYER) {
      world.player.equippedItems.mount = undefined;
    }
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({ player: { serial: PLAYER } });
});

describe('dismount', () => {
  // Asked every cycle, so the common case has to cost nothing and say nothing
  it('does nothing when there is no mount', async () => {
    const { dismount } = await loadMount();

    expect(dismount()).toBe(true);
    expect(world.player.use).not.toHaveBeenCalled();
    expect(world.log).not.toHaveBeenCalled();
  });

  it('double-clicks the player to get off', async () => {
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    dismountWorks();
    const { dismount } = await loadMount();

    expect(dismount()).toBe(true);
    expect(world.player.use).toHaveBeenCalledWith(PLAYER);
  });

  // A cursor left open by the last swing would swallow the double-click
  it('cancels a leftover target cursor first', async () => {
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    dismountWorks();
    const { dismount } = await loadMount();

    dismount();

    expect(world.target.cancel).toHaveBeenCalled();
  });

  // The action is asynchronous, so the swing must not start until the layer has actually cleared
  it('reissues the double-click when the layer does not clear', async () => {
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    const { dismount } = await loadMount();

    expect(dismount()).toBe(false);
    expect(world.player.use).toHaveBeenCalledTimes(DISMOUNT_ATTEMPTS);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('gave up'));
  });

  // Once per spell of being mounted, not once per cycle. A mount the shard will not let go of is
  // asked about every cycle until the stall watchdog fires, and one line each would bury the rest
  // of the run's output under hundreds of copies of the same sentence.
  it('says it is getting off once however many cycles stay stuck', async () => {
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    const { dismount } = await loadMount();

    dismount();
    dismount();
    dismount();

    const said = world.log.mock.calls.filter(([line]) =>
      String(line).includes('getting off before working'),
    );
    expect(said).toHaveLength(1);
  });

  // But a fresh mount is fresh news: latched off again by the dismount that worked
  it('says so again the next time you end up on something', async () => {
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    dismountWorks();
    const { dismount } = await loadMount();

    dismount();
    world.player.equippedItems.mount = item({ serial: 2, graphic: 0x3ebb });
    dismount();

    const said = world.log.mock.calls.filter(([line]) =>
      String(line).includes('getting off before working'),
    );
    expect(said).toHaveLength(2);
  });
});
