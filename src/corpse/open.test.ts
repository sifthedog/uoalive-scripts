import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type FakeWorld, installGlobals, item } from '../test-support/uo.js';
import { CORPSE_GRAPHIC } from './config.js';
import { describeHeld, open } from './open.js';

const DELAYS = { openDelay: 800, settlePoll: 100, settleTimeout: 400 };

const SERIAL = 0x40000001;

let world: FakeWorld;

const corpse = (contents?: Item[]) =>
  item({ serial: SERIAL, graphic: CORPSE_GRAPHIC, contents });

beforeEach(() => {
  world = installGlobals();
});

describe('open', () => {
  it('double-clicks the corpse once and hands back what it holds', () => {
    const feather = item({ serial: 2, graphic: 0x1bd1, amount: 5 });
    world.client.findObject = vi.fn(() => corpse([feather]));

    expect(open(SERIAL, DELAYS)).toEqual({ outcome: 'opened', contents: [feather] });
    expect(world.player.use).toHaveBeenCalledTimes(1);
    expect(world.player.use).toHaveBeenCalledWith(SERIAL);
  });

  it('reads an empty answer as an empty corpse', () => {
    world.client.findObject = vi.fn(() => corpse([]));

    expect(open(SERIAL, DELAYS).outcome).toBe('empty');
  });

  it('reports a corpse the client stopped tracking rather than reading it as empty', () => {
    world.client.findObject = vi.fn(() => undefined);

    expect(open(SERIAL, DELAYS).outcome).toBe('gone');
  });

  it('reads a contents that would not answer as unreadable and not as empty', () => {
    const silent = corpse();
    Object.defineProperty(silent, 'contents', {
      get: () => {
        throw new Error('Unexpected end of JSON input');
      },
    });
    world.client.findObject = vi.fn(() => silent);

    expect(open(SERIAL, DELAYS).outcome).toBe('unreadable');
  });

  it('waits for a corpse that answers late rather than giving up on the first read', () => {
    // Three silent reads is more than the one poll-free open makes, so this is 'unreadable' without
    // the settle loop
    let reads = 0;
    world.client.findObject = vi.fn(() => (++reads <= 3 ? corpse(undefined) : corpse([])));

    expect(open(SERIAL, DELAYS).outcome).toBe('empty');
  });
});

describe('describeHeld', () => {
  it('says so plainly when there is nothing in it', () => {
    expect(describeHeld([], 40)).toBe('nothing');
  });

  it('sums the stacks by name, which is what you are looking for your gear by', () => {
    const held = [
      item({ serial: 1, graphic: 0x1bd1, name: 'feather', amount: 5 }),
      item({ serial: 2, graphic: 0x1bd1, name: 'feather', amount: 3 }),
    ];

    expect(describeHeld(held, 40)).toBe('feather x8');
  });

  it('falls back to the art and hue for a stack the client has not named', () => {
    expect(describeHeld([item({ serial: 1, graphic: 0x13ff, hue: 2 })], 40)).toBe('0x13ff/2 x1');
  });

  it('stops listing after the limit and counts the rest', () => {
    const held = [
      item({ serial: 1, graphic: 0x13ff, name: 'katana' }),
      item({ serial: 2, graphic: 0x1bd1, name: 'feather' }),
      item({ serial: 3, graphic: 0x0eed, name: 'gold' }),
    ];

    expect(describeHeld(held, 1)).toBe('katana x1, and 2 more');
  });
});
