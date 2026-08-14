import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { untilLanded } from './retry.js';

let world: FakeWorld;

const attempt = (options: { act?: () => void; landed: () => boolean }) =>
  untilLanded({
    label: 'equip pickaxe',
    attempts: 3,
    timeoutMs: 400,
    pollMs: 100,
    act: options.act ?? (() => {}),
    landed: options.landed,
  });

beforeEach(() => {
  world = installGlobals();
});

describe('untilLanded', () => {
  // The call returns before the world has changed, so a fixed sleep is a guess at how long the
  // shard takes and hands the next action a character that is not ready
  it('polls for the proof rather than trusting the call', () => {
    let ready = false;
    world.sleep.mockImplementation(() => {
      ready = true;
    });

    expect(attempt({ landed: () => ready })).toBe(true);
    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  it('stops polling the moment it has landed', () => {
    expect(attempt({ landed: () => true })).toBe(true);
    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  // A throttled action looks exactly like one that never arrived, so reissue rather than give up
  it('reissues once the timeout is out, up to the attempts it was given', () => {
    const act = vi.fn();

    expect(attempt({ act, landed: () => false })).toBe(false);
    expect(act).toHaveBeenCalledTimes(3);
    expect(world.sleep).toHaveBeenCalledTimes(12);
  });

  it('says which attempt did not land, and says when it has given up', () => {
    attempt({ landed: () => false });

    expect(world.log).toHaveBeenCalledWith('equip pickaxe: attempt 1 did not land, reissuing');
    expect(world.log).toHaveBeenCalledWith('equip pickaxe: gave up');
  });

  it('stays quiet when the first attempt works', () => {
    attempt({ landed: () => true });

    expect(world.log).not.toHaveBeenCalled();
  });
});
