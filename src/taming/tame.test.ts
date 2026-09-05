import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, mobile, type FakeWorld } from '../test-support/uo.js';
import { OUTCOME_TEXT, TAME_WAIT_SLICE } from './config.js';

let world: FakeWorld;

const loadTame = async () => import('./tame.js');

// The two-stage wait needs a journal that answers differently per call, which no other fixture does
const says = (...answers: (string | undefined)[]) => {
  world.journal.waitForTextAny = vi.fn(() => answers.shift());
};

const creature = (isRenamable = false) =>
  mobile({ serial: 0x1234, graphic: 0x00d0, isRenamable });

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('outcomeFor', () => {
  it('maps the two phrases the shard was read for', async () => {
    const { outcomeFor } = await loadTame();

    expect(outcomeFor('It seems to accept you as master')).toBe('tamed');
    expect(outcomeFor('You fail to tame the creature')).toBe('failed');
  });

  it('knows the world save and the throttle for what they are', async () => {
    const { outcomeFor } = await loadTame();

    expect(outcomeFor('The world is saving')).toBe('saving');
    expect(outcomeFor('You must wait')).toBe('throttled');
  });
});

// The start line is still in the journal when the second wait goes out, so a resolution list that
// contained it would match itself and spin
describe('RESOLUTION_TEXT', () => {
  it('leaves out every phrase that only means the attempt began', async () => {
    const { RESOLUTION_TEXT } = await loadTame();

    for (const phrase of OUTCOME_TEXT.starting) {
      expect(RESOLUTION_TEXT).not.toContain(phrase);
    }
  });

  it('still carries both resolutions', async () => {
    const { RESOLUTION_TEXT } = await loadTame();

    expect(RESOLUTION_TEXT).toContain('It seems to accept you as master');
    expect(RESOLUTION_TEXT).toContain('You fail to tame the creature');
  });
});

describe('tameOnce', () => {
  it('uses the skill against the creature rather than through a cursor of its own', async () => {
    const { tameOnce } = await loadTame();

    tameOnce(0x1234);

    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.AnimalTaming, 0x1234);
  });

  it('clears the target queue first', async () => {
    const { tameOnce } = await loadTame();

    tameOnce(0x1234);

    expect(world.target.clearQueue).toHaveBeenCalled();
  });

  it('cancels a live cursor, and only a live one', async () => {
    const { tameOnce } = await loadTame();

    tameOnce(0x1234);
    expect(world.target.cancel).not.toHaveBeenCalled();

    world.target.open = true;
    tameOnce(0x1234);
    expect(world.target.cancel).toHaveBeenCalled();
  });

  // A line still in the journal from the last attempt would be read as this one's outcome
  it('clears the journal before the use, not after it', async () => {
    const { tameOnce } = await loadTame();

    tameOnce(0x1234);

    const [cleared] = world.journal.clear.mock.invocationCallOrder;
    const [used] = world.player.useSkill.mock.invocationCallOrder;

    expect(cleared).toBeLessThan(used);
  });

  it('takes a refusal at the first wait as the answer, without waiting again', async () => {
    says('You must wait');
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('throttled');
    expect(world.journal.waitForTextAny).toHaveBeenCalledTimes(1);
  });

  it('waits a second time for the attempt it was told had started', async () => {
    says('You start to tame the creature', 'It seems to accept you as master');
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('tamed');
  });

  it('reads the failure the same way', async () => {
    says('You start to tame the creature', 'You fail to tame the creature');
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('failed');
  });

  it('offers the second wait the resolutions only', async () => {
    says('You start to tame the creature', 'You fail to tame the creature');
    const { RESOLUTION_TEXT, tameOnce } = await loadTame();

    tameOnce(0x1234);

    expect(world.journal.waitForTextAny.mock.calls[1][0]).toEqual(RESOLUTION_TEXT);
  });

  // Not 'failed': an attempt the shard never answered is a timeout to raise, not a roll that missed
  it('says an attempt that started and never resolved is pending', async () => {
    says('You start to tame the creature');
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('pending');
  });

  it('comes back unknown when nothing at all was said', async () => {
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('unknown');
  });

  // A shard that words its taming differently leaves the journal silent, and the flag is the one
  // proof that does not go through it
  it('takes the creature becoming renamable as a tame when the shard says nothing', async () => {
    const { tameOnce } = await loadTame();
    world.client.findObject.mockReturnValue(creature());
    world.player.useSkill.mockImplementation(() => {
      world.client.findObject.mockReturnValue(creature(true));
    });

    expect(tameOnce(0x1234)).toBe('tamed');
  });

  it('does not read a creature that was already someone\'s pet as a fresh tame', async () => {
    const { tameOnce } = await loadTame();
    world.client.findObject.mockReturnValue(creature(true));

    expect(tameOnce(0x1234)).toBe('unknown');
  });

  // The animal walks for as long as the attempt takes, so the wait cannot be one long block
  it('waits in slices rather than in one go', async () => {
    const { tameOnce } = await loadTame();

    tameOnce(0x1234);

    expect(world.journal.waitForTextAny.mock.calls[0][2]).toBe(TAME_WAIT_SLICE);
  });

  it('gives the caller a turn between the slices', async () => {
    const between = vi.fn();
    const { tameOnce } = await loadTame();

    tameOnce(0x1234, between);

    expect(between).toHaveBeenCalled();
  });

  it('offers no turn at all once the shard has answered', async () => {
    says('It seems to accept you as master');
    const between = vi.fn();
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234, between)).toBe('tamed');
    expect(between).not.toHaveBeenCalled();
  });

  // The line lands while the caller is mid-step, and waitForTextAny reads the journal as it stands
  it('still reads a resolution that landed during a step', async () => {
    says(undefined, 'You start to tame the creature', undefined, 'You fail to tame the creature');
    const { tameOnce } = await loadTame();

    expect(tameOnce(0x1234, vi.fn())).toBe('failed');
  });

  it('reads a creature the shard will not let you tame, and has a reason for it', async () => {
    says('You have no chance of taming this creature');
    const { STOP_REASON, tameOnce } = await loadTame();

    expect(tameOnce(0x1234)).toBe('hopeless');
    expect(STOP_REASON.hopeless).toBeTruthy();
  });
});
