import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, mobile, type FakeWorld } from '../test-support/uo.js';
import { HUNT_RADIUS, PET_NAME } from './config.js';

let world: FakeWorld;

const loadHunt = async () => import('./hunt.js');

const HORSE = 0x00c8;

// The player sits at 100,100 in the fixture, so `away` is the Chebyshev distance
const horse = (
  serial: number,
  away: number,
  fields: Partial<Mobile> = {},
): Mobile => mobile({ serial, graphic: HORSE, x: 100 + away, y: 100, name: 'a horse', ...fields });

const inSight = (...found: Mobile[]) => {
  world.client.findAllMobilesOfType = vi.fn(() => found);
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('nextQuarry', () => {
  it('asks for the same body in any colour', async () => {
    const { nextQuarry } = await loadHunt();

    nextQuarry(HORSE);

    expect(world.client.findAllMobilesOfType).toHaveBeenCalledWith(
      HORSE,
      null,
      null,
      null,
      HUNT_RADIUS,
    );
  });

  it('takes the nearest of them', async () => {
    inSight(horse(0x11, 6), horse(0x22, 2), horse(0x33, 4));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)?.quarry.serial).toBe(0x22);
  });

  it('says how many of the type are in sight', async () => {
    inSight(horse(0x11, 1), horse(0x22, 2), horse(0x33, 3));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)?.inSight).toBe(3);
  });

  it('comes back with nothing when there are none', async () => {
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  // graphic reads 0 for an entity the client is no longer tracking
  it('leaves out one the client has stopped tracking', async () => {
    inSight(horse(0x11, 2, { graphic: 0 }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  it('leaves out a dead one', async () => {
    inSight(horse(0x11, 2, { isDead: true }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  // True for pets and followers, so this is every animal the run has already kept
  it('leaves out one that is already somebody\'s pet', async () => {
    inSight(horse(0x11, 2, { isRenamable: true }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  // Released rather than kept: the slot came back but the name did not
  it('leaves out one already named for this run', async () => {
    inSight(horse(0x11, 2, { name: PET_NAME }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  it('matches that name without regard to case', async () => {
    inSight(horse(0x11, 2, { name: PET_NAME.toUpperCase() }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  // The scan takes a range of its own, but what it means next to these arguments is undocumented
  it('measures the distance itself rather than trusting the scan', async () => {
    inSight(horse(0x11, HUNT_RADIUS + 1));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)).toBeUndefined();
  });

  it('keeps one exactly at the radius', async () => {
    inSight(horse(0x11, HUNT_RADIUS));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)?.quarry.serial).toBe(0x11);
  });

  it('leaves out one the run is finished with', async () => {
    inSight(horse(0x11, 2), horse(0x22, 4));
    const { leaveOut, nextQuarry } = await loadHunt();

    leaveOut(0x11);

    expect(nextQuarry(HORSE)?.quarry.serial).toBe(0x22);
  });

  // Names read empty until the client has tooltip data, and only the one about to be taken is asked
  it('asks the tooltip for a name the client does not have yet', async () => {
    inSight(horse(0x11, 2, { name: '' }));
    world.client.queryItemOPL = vi.fn(() => ({ name: 'a fine horse' }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)?.quarry.name).toBe('a fine horse');
  });

  it('drops it when the tooltip says it was already this run\'s', async () => {
    inSight(horse(0x11, 2, { name: '' }), horse(0x22, 4));
    world.client.queryItemOPL = vi.fn(() => ({ name: PET_NAME }));
    const { nextQuarry } = await loadHunt();

    expect(nextQuarry(HORSE)?.quarry.serial).toBe(0x22);
  });
});
