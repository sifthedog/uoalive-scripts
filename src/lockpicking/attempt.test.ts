import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { LOCKPICK_GRAPHICS, OUTCOME_TEXT } from './config.js';

const LOCKPICK = [...LOCKPICK_GRAPHICS][0];
const BOX = 0x40001111;
const PICK = 0x40002222;

let world: FakeWorld;

// attempt.ts pulls in picks.ts, which remembers the graphic it learned
const loadAttempt = async () => import('./attempt.js');

// A pack whose lockpick stack shrinks the moment the lockpick is double-clicked, which is what a
// broken pick looks like on a shard that says nothing about it
const packOf = (amounts: number[]): void => {
  let used = 0;

  Object.defineProperty(world.player, 'backpack', {
    configurable: true,
    get: () => ({
      serial: 0x40000000,
      contents: [item({ serial: PICK, graphic: LOCKPICK, amount: amounts[used] })],
    }),
  });

  world.player.use.mockImplementation((serial: number) => {
    if (serial === PICK) {
      used = Math.min(used + 1, amounts.length - 1);
    }
  });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
  packOf([10, 10]);
});

describe('outcomeFor', () => {
  it('maps a phrase back to its bucket', async () => {
    const { outcomeFor } = await loadAttempt();

    expect(outcomeFor('You are unable to pick the lock')).toBe('failed');
    expect(outcomeFor('You broke the lockpick')).toBe('broke');
    expect(outcomeFor('This does not appear to be locked')).toBe('notLocked');
  });

  // The shared wordings are listed in tooHard, so a lock beyond the character is not read as silence
  it('reads the unskilled wordings as a lock that cannot be picked', async () => {
    const { outcomeFor } = await loadAttempt();

    expect(outcomeFor('You are not skilled enough')).toBe('tooHard');
  });

  it('knows the world save for what it is', async () => {
    const { outcomeFor } = await loadAttempt();

    expect(outcomeFor('The world is saving')).toBe('saving');
  });

  it('offers every phrase to the journal, not just one bucket', async () => {
    const { ALL_OUTCOME_TEXT } = await loadAttempt();

    expect(ALL_OUTCOME_TEXT).toContain('You must wait');
    expect(ALL_OUTCOME_TEXT).toContain('That is too far away');
  });
});

describe('STOP_REASON', () => {
  it('has a reason for every outcome no retry gets past', async () => {
    const { STOP_REASON } = await loadAttempt();

    for (const outcome of ['picked', 'tooHard', 'notLocked', 'tooFar', 'noPicks'] as const) {
      expect(STOP_REASON[outcome]).toBeTruthy();
    }
  });

  it('leaves the outcomes the loop retries alone', async () => {
    const { STOP_REASON } = await loadAttempt();

    expect(STOP_REASON.failed).toBeUndefined();
    expect(STOP_REASON.broke).toBeUndefined();
    expect(STOP_REASON.throttled).toBeUndefined();
  });
});

describe('pickOnce', () => {
  it('clicks the container before the lockpick', async () => {
    const { pickOnce } = await loadAttempt();

    pickOnce(BOX, PICK);

    expect(world.player.use.mock.calls.map(([serial]) => serial)).toEqual([BOX, PICK]);
  });

  // The container's own 'this is locked' line would otherwise be read as the attempt's outcome
  it('clears the journal after the container click, not before it', async () => {
    const { pickOnce } = await loadAttempt();

    pickOnce(BOX, PICK);

    const [poke] = world.player.use.mock.invocationCallOrder;
    const [cleared] = world.journal.clear.mock.invocationCallOrder;

    expect(cleared).toBeGreaterThan(poke);
  });

  it('answers the cursor with the container', async () => {
    const { pickOnce } = await loadAttempt();

    pickOnce(BOX, PICK);

    expect(world.target.waitTargetEntity).toHaveBeenCalledWith(BOX, expect.any(Number));
  });

  it('reads the shard back', async () => {
    const { pickOnce } = await loadAttempt();
    world.journal.waitForTextAny.mockReturnValue(OUTCOME_TEXT.failed[0]);

    expect(pickOnce(BOX, PICK)).toBe('failed');
  });

  // A shard that words its lockpicking differently leaves the journal silent, and a stack keeps its
  // serial while its amount drops, so the count is the only proof a pick broke
  it('takes a shrinking stack as a broken pick when the shard says nothing', async () => {
    const { pickOnce } = await loadAttempt();
    packOf([10, 9]);

    expect(pickOnce(BOX, PICK)).toBe('broke');
  });

  it('says so rather than guessing when nothing moved and nothing was said', async () => {
    const { pickOnce } = await loadAttempt();

    expect(pickOnce(BOX, PICK)).toBe('unknown');
  });

  it('reports a cursor that never opened', async () => {
    const { pickOnce } = await loadAttempt();
    world.target.waitTargetEntity.mockReturnValue(false);

    expect(pickOnce(BOX, PICK)).toBe('noCursor');
    expect(world.target.cancel).toHaveBeenCalled();
  });

  // The refusal that explains the missing cursor usually landed a moment late
  it('prefers a late refusal to blaming the cursor', async () => {
    const { pickOnce } = await loadAttempt();
    world.target.waitTargetEntity.mockReturnValue(false);
    world.journal.waitForTextAny.mockReturnValue(OUTCOME_TEXT.tooFar[0]);

    expect(pickOnce(BOX, PICK)).toBe('tooFar');
  });

  it('leaves the cursor alone when there is none to cancel', async () => {
    const { pickOnce } = await loadAttempt();

    pickOnce(BOX, PICK);

    expect(world.target.cancel).not.toHaveBeenCalled();
  });
});
