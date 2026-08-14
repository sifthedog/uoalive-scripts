import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, mobile, type FakeWorld } from '../test-support/uo.js';
import { approach, distanceTo, hex, isMobile, nameOf } from './entity.js';

let world: FakeWorld;

beforeEach(() => {
  world = installGlobals({ player: { x: 50, y: 50 } });
});

describe('hex', () => {
  // The tinkering gump, which prints as 0x-3266af2f without the shift
  it('prints a serial the client reports as a negative int', () => {
    expect(hex(-0x3266af2f)).toBe('0xcd9950d1');
  });

  it('prints an ordinary graphic', () => {
    expect(hex(0x1bdd)).toBe('0x1bdd');
  });
});

describe('distanceTo', () => {
  // Chebyshev, because a diagonal step covers a tile of x and a tile of y at once
  it('counts a diagonal as one step per tile, not two', () => {
    expect(distanceTo({ x: 52, y: 52 })).toBe(2);
    expect(distanceTo({ x: 52, y: 50 })).toBe(2);
    expect(distanceTo({ x: 50, y: 50 })).toBe(0);
  });
});

describe('isMobile', () => {
  it('tells a mobile from an item without a round trip', () => {
    expect(isMobile(mobile({ serial: 1, graphic: 0xa9 }))).toBe(true);
    expect(isMobile(item({ serial: 2, graphic: 0x19b7 }))).toBe(false);
  });
});

describe('nameOf', () => {
  it('prefers the name the client has', () => {
    expect(nameOf({ name: 'Bessie', serial: 0x40000001 })).toBe('Bessie');
  });

  // Names are empty until the client has tooltip data for the entity
  it('falls back to the serial', () => {
    expect(nameOf({ serial: 0x40000001 })).toBe('0x40000001');
  });
});

describe('approach', () => {
  const beetle = (x: number, y: number) => mobile({ serial: 0x77, graphic: 0xa9, x, y });

  const walkTo = (step: (spot: { x: number; y: number }) => boolean) =>
    approach(0x77, { label: 'smelt', range: 2, maxSteps: 4, step });

  it('is already there when the target is inside range', () => {
    world.client.findObject.mockReturnValue(beetle(51, 51));

    expect(walkTo(() => true)).toBeDefined();
  });

  // The pet follows you, so its coordinates go stale within a cycle - walking at where it was when
  // the approach started would be walking at nothing
  it('re-resolves the target on every step', () => {
    let x = 60;
    world.client.findObject.mockImplementation(() => beetle(x, 50));

    const found = walkTo(() => {
      x -= 4;
      return true;
    });

    expect(found).toBeDefined();
    expect(world.client.findObject.mock.calls.length).toBeGreaterThan(1);
  });

  it('gives up when the target stops resolving', () => {
    world.client.findObject.mockReturnValue(undefined);

    expect(walkTo(() => true)).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('lost track'));
  });

  it('gives up on something that resolves to an item rather than a mobile', () => {
    world.client.findObject.mockReturnValue(item({ serial: 0x77, graphic: 0x19b7 }));

    expect(walkTo(() => true)).toBeUndefined();
  });

  it('gives up when a step does not move the character', () => {
    world.client.findObject.mockReturnValue(beetle(60, 50));

    expect(walkTo(() => false)).toBeUndefined();
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('cannot reach'));
  });

  // The ore keeps, so a walk that never closes costs a pass rather than the run
  it('stops after the steps it was given rather than walking forever', () => {
    world.client.findObject.mockReturnValue(beetle(600, 50));
    const step = vi.fn(() => true);

    expect(walkTo(step)).toBeUndefined();
    expect(step).toHaveBeenCalledTimes(4);
    expect(world.log).toHaveBeenCalledWith(expect.stringContaining('after 4 steps'));
  });
});
