import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { SAVE_POLL, SAVE_WAIT } from './config.js';
import { isSaving, waitOutSave } from './save.js';

let world: FakeWorld;

// sleep is a no-op in the fake world, so the whole wait runs instantly and the slices can be
// counted: this is how many it would take to sit out a save the completion line never ended
const SLICES = SAVE_WAIT / SAVE_POLL;

const journalSays = (...lines: string[]) => {
  world.journal.containsText.mockImplementation((text: string) =>
    lines.some((line) => line.includes(text)),
  );
};

beforeEach(() => {
  world = installGlobals();
});

describe('isSaving', () => {
  it('recognises the shard writing its world file', () => {
    journalSays('The world is saving, please wait.');

    expect(isSaving()).toBe(true);
  });

  it('says nothing is happening on a quiet journal', () => {
    expect(isSaving()).toBe(false);
  });
});

describe('waitOutSave', () => {
  // The line that got us here is still in the journal, and a shard that words both ends of the save
  // alike would otherwise have that stale line end the wait before the save did
  it('clears the journal before it starts listening', () => {
    waitOutSave();

    expect(world.journal.clear).toHaveBeenCalled();
  });

  it('stops as soon as the shard says the save is done', () => {
    journalSays('World save complete');

    waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  // The fallback for a shard whose completion wording SAVE_DONE_TEXT does not have. Standing still
  // for SAVE_WAIT is the cost of missing it, which is survivable; waiting forever would not be.
  it('gives up on the completion line rather than waiting forever', () => {
    waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(SLICES);
  });

  // Sliced rather than slept through for exactly this: a minute is long enough to be killed
  // standing there, and one blocking sleep would carry on regardless
  it('abandons the wait when the run has a reason to stop', () => {
    world.player.isDead = true;

    waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(1);
  });
});
