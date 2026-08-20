import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { STEALTH_TEXT } from './config.js';

let world: FakeWorld;

const loadStealth = async () => import('./stealth.js');

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
  world.player.isHidden = true;
});

describe('outcomeFor', () => {
  it('maps a phrase back to its bucket', async () => {
    const { outcomeFor } = await loadStealth();

    expect(outcomeFor(STEALTH_TEXT.quietly[0])).toBe('quietly');
    expect(outcomeFor(STEALTH_TEXT.failed[0])).toBe('failed');
    expect(outcomeFor(STEALTH_TEXT.armour[0])).toBe('armour');
  });

  // The shared wordings are listed in notHiddenWell, so a gate the character has not cleared is not
  // read as silence
  it('reads the unskilled wordings as hiding that is not good enough', async () => {
    const { outcomeFor } = await loadStealth();

    expect(outcomeFor('You are not skilled enough')).toBe('notHiddenWell');
  });
});

describe('stealthOnce', () => {
  it('uses the skill and reads the shard back', async () => {
    const { stealthOnce } = await loadStealth();
    world.journal.waitForTextAny.mockReturnValue(STEALTH_TEXT.quietly[0]);

    expect(stealthOnce()).toBe('quietly');
    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.Stealth);
  });

  it('reads a failure back', async () => {
    const { stealthOnce } = await loadStealth();
    world.journal.waitForTextAny.mockReturnValue(STEALTH_TEXT.failed[0]);

    expect(stealthOnce()).toBe('failed');
  });

  // Or the line the last attempt produced answers this one
  it('clears the journal before using the skill', async () => {
    const { stealthOnce } = await loadStealth();

    stealthOnce();

    const [cleared] = world.journal.clear.mock.invocationCallOrder;
    const [used] = world.player.useSkill.mock.invocationCallOrder;

    expect(cleared).toBeLessThan(used);
  });

  it('reads the flag going down as the attempt having lost', async () => {
    const { stealthOnce } = await loadStealth();
    world.player.useSkill.mockImplementation(() => {
      world.player.isHidden = false;
    });

    expect(stealthOnce()).toBe('failed');
  });

  it('says so rather than guessing when the shard says nothing and we are still hidden', async () => {
    const { stealthOnce } = await loadStealth();

    expect(stealthOnce()).toBe('unknown');
  });

  // A refusal never revealed us, so a run that started revealed must not read one as a failure
  it('does not read a flag that was already down as a failure', async () => {
    const { stealthOnce } = await loadStealth();
    world.player.isHidden = false;

    expect(stealthOnce()).toBe('unknown');
  });
});
