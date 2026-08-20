import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';
import { HIDE_TEXT } from './config.js';

let world: FakeWorld;

const loadHide = async () => import('./hide.js');

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('outcomeFor', () => {
  it('maps a phrase back to its bucket', async () => {
    const { outcomeFor } = await loadHide();

    expect(outcomeFor(HIDE_TEXT.hidden[0])).toBe('hidden');
    expect(outcomeFor(HIDE_TEXT.failed[0])).toBe('failed');
    expect(outcomeFor(HIDE_TEXT.busy[0])).toBe('busy');
  });

  it('knows the world save for what it is', async () => {
    const { outcomeFor } = await loadHide();

    expect(outcomeFor('The world is saving')).toBe('saving');
  });

  it('offers every phrase to the journal, not just one bucket', async () => {
    const { ALL_HIDE_TEXT } = await loadHide();

    expect(ALL_HIDE_TEXT).toContain('You must wait');
    expect(ALL_HIDE_TEXT).toContain(HIDE_TEXT.hidden[0]);
  });
});

describe('hideOnce', () => {
  it('uses the skill with nothing to target', async () => {
    const { hideOnce } = await loadHide();

    hideOnce();

    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.Hiding);
  });

  // A line still in the journal from the last attempt would be read as this one's outcome
  it('clears the journal before the use, not after it', async () => {
    const { hideOnce } = await loadHide();

    hideOnce();

    const [cleared] = world.journal.clear.mock.invocationCallOrder;
    const [used] = world.player.useSkill.mock.invocationCallOrder;

    expect(cleared).toBeLessThan(used);
  });

  it('reads the shard back', async () => {
    const { hideOnce } = await loadHide();
    world.journal.waitForTextAny.mockReturnValue(HIDE_TEXT.failed[0]);

    expect(hideOnce()).toBe('failed');
  });

  // A shard that words its hiding differently leaves the journal silent, and the client's flag is
  // the one proof that does not go through it
  it('takes the flag going up as a hide when the shard says nothing', async () => {
    const { hideOnce } = await loadHide();
    world.player.useSkill.mockImplementation(() => {
      world.player.isHidden = true;
    });

    expect(hideOnce()).toBe('hidden');
  });

  // Re-hiding while hidden is how the skill is trained, so the flag proves nothing about this use
  it('does not read a character who was already hidden as a fresh hide', async () => {
    const { hideOnce } = await loadHide();
    world.player.isHidden = true;

    expect(hideOnce()).toBe('unknown');
  });

  it('says so rather than guessing when nothing was said and nothing changed', async () => {
    const { hideOnce } = await loadHide();

    expect(hideOnce()).toBe('unknown');
  });
});
