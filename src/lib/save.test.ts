import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { createSaveWatch } from './save.js';

const SAVE_WAIT = 60_000;
const SAVE_POLL = 1000;

// sleep is a no-op in the fake world, so the whole wait runs instantly and the slices can be
// counted: this is how many it would take to sit out a save the completion line never ended
const SLICES = SAVE_WAIT / SAVE_POLL;

let world: FakeWorld;
let stopReason: () => string | undefined;
let onDone: ReturnType<typeof vi.fn>;

const watch = () =>
  createSaveWatch({
    savingText: ['The world is saving'],
    doneText: ['World save complete'],
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    onDone,
  });

const journalSays = (...lines: string[]) => {
  world.journal.containsText.mockImplementation((text: string) =>
    lines.some((line) => line.includes(text)),
  );
};

beforeEach(() => {
  world = installGlobals();
  stopReason = () => undefined;
  onDone = vi.fn();
});

describe('isSaving', () => {
  it('recognises the shard writing its world file', () => {
    journalSays('The world is saving, please wait.');

    expect(watch().isSaving()).toBe(true);
  });

  it('says nothing is happening on a quiet journal', () => {
    expect(watch().isSaving()).toBe(false);
  });
});

describe('waitOutSave', () => {
  // The line that got us here is still in the journal, and a shard that words both ends of the save
  // alike would otherwise have that stale line end the wait before the save did
  it('clears the journal before it starts listening', () => {
    watch().waitOutSave();

    expect(world.journal.clear).toHaveBeenCalled();
  });

  it('stops as soon as the shard says the save is done', () => {
    journalSays('World save complete');

    watch().waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  // The fallback for a shard whose completion wording doneText does not have. Standing still for
  // waitMs is the cost of missing it, which is survivable; waiting forever would not be.
  it('gives up on the completion line rather than waiting forever', () => {
    watch().waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(SLICES);
  });

  // Sliced rather than slept through for exactly this: a minute is long enough to be killed
  // standing there, and one blocking sleep would carry on regardless
  it('abandons the wait when the run has a reason to stop', () => {
    stopReason = () => 'you are dead';

    watch().waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(1);
  });

  // The next beat should start a full interval from here rather than landing on top of the line
  // this path just printed - including on the way out, which it used to return straight past
  it('hands back to the heartbeat however the wait ended', () => {
    journalSays('World save complete');
    watch().waitOutSave();
    expect(onDone).toHaveBeenCalledTimes(1);

    onDone.mockClear();
    stopReason = () => 'you are dead';
    watch().waitOutSave();
    expect(onDone).toHaveBeenCalledTimes(1);
  });
});
