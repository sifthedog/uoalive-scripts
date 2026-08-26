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

// A journal that behaves like the client's - lines accumulate, clear() empties it. The shared fake's
// clear() is inert, which is why the race these cover went unnoticed.
const liveJournal = () => {
  let lines: string[] = [];

  world.journal.containsText.mockImplementation((text: string) =>
    lines.some((line) => line.includes(text)),
  );
  world.journal.clear.mockImplementation(() => {
    lines = [];
  });

  return { say: (...said: string[]) => lines.push(...said) };
};

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
    const shard = liveJournal();
    shard.say('The world is saving, please wait.');

    let slept = 0;
    world.sleep.mockImplementation(() => {
      if (++slept === 3) {
        shard.say('World save complete');
      }
    });

    watch().waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(3);
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

// A save can start and finish inside one swing - a dig alone waits up to DIG_TIMEOUT - so by the time
// the loop reads the journal both lines are usually already in it.
describe('a save that finished before the wait began', () => {
  it('does not stand there waiting for a line that has already been said', () => {
    const shard = liveJournal();
    shard.say('The world is saving, please wait.', 'World save complete');

    watch().waitOutSave();

    expect(world.sleep).not.toHaveBeenCalled();
  });

  it('leaves the journal clear, so the next cycle does not read the save as still running', () => {
    const shard = liveJournal();
    shard.say('The world is saving, please wait.', 'World save complete');
    const save = watch();

    save.waitOutSave();

    expect(save.isSaving()).toBe(false);
  });

  it('still waits out a save the shard has not finished', () => {
    const shard = liveJournal();
    shard.say('The world is saving, please wait.');

    watch().waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(SLICES);
  });

  // The reason the journal is cleared at all: without it the last save's completion would end the
  // next save's wait before the shard had even started writing.
  it("does not let the last save's completion end the next one", () => {
    const shard = liveJournal();
    const save = watch();

    shard.say('The world is saving, please wait.', 'World save complete');
    save.waitOutSave();

    shard.say('The world is saving, please wait.');
    world.sleep.mockClear();
    save.waitOutSave();

    expect(world.sleep).toHaveBeenCalledTimes(SLICES);
  });
});
