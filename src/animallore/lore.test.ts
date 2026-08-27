import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

// config is mocked per test so the polls do not cost real time, and so the close-button fallback can
// be pinned both ways
const loadLore = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    LORE_TIMEOUT: 300,
    LORE_POLL: 100,
    ...config,
  }));

  return import('./lore.js');
};

// Gump.findOrWait answers with one of these; `exists` is what says whether close() worked
const gump = (overrides: Partial<{ exists: boolean }> = {}) => ({
  close: vi.fn(),
  reply: vi.fn(),
  exists: false,
  ...overrides,
});

// The shard says nothing when a read works, so the gump opening is the whole of the proof
const opens = (found: ReturnType<typeof gump>) => {
  world.gump.findOrWait = vi.fn(() => found);
};

const says = (line: string) => {
  world.journal.containsText = vi.fn((text: string) => text === line);
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals();
});

describe('loreOnce', () => {
  it('uses the skill against the creature rather than through a cursor of its own', async () => {
    const { loreOnce } = await loadLore();

    loreOnce(0x1234);

    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.AnimalLore, 0x1234);
  });

  // A cursor left open by whatever ran last would swallow this read
  it('clears the target queue first', async () => {
    const { loreOnce } = await loadLore();

    loreOnce(0x1234);

    expect(world.target.clearQueue).toHaveBeenCalled();
  });

  // An unconditional cancel just before an action was measured leaving the cursor that followed shut
  it('cancels a live cursor, and only a live one', async () => {
    const { loreOnce } = await loadLore();

    loreOnce(0x1234);
    expect(world.target.cancel).not.toHaveBeenCalled();

    world.target.open = true;
    loreOnce(0x1234);
    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('reads the gump opening as a read that landed, since the shard says nothing', async () => {
    opens(gump());
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('lored');
  });

  it('closes the gump it read', async () => {
    const found = gump();
    opens(found);
    const { loreOnce } = await loadLore();

    loreOnce(0x1234);

    expect(found.close).toHaveBeenCalled();
  });

  // A failed skill check still rolled the skill, so it is training rather than a refusal
  it('tells a missed read from a refused one', async () => {
    says("You can't think of anything you know offhand");
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('missed');
  });

  it('reads the shard asking it to wait', async () => {
    says('You must wait');
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('throttled');
  });

  it('reads being out of range', async () => {
    says('That is too far away');
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('tooFar');
  });

  it('reads a creature the skill does not apply to', async () => {
    says("That's not an animal");
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('notAnimal');
  });

  // Neither a gump nor a sentence: the wordings are guesses, and this is what makes a wrong one show
  it('comes back unknown when nothing at all happened', async () => {
    const { loreOnce } = await loadLore();

    expect(loreOnce(0x1234)).toBe('unknown');
  });

  describe('a gump that will not close', () => {
    it('presses the configured button', async () => {
      const found = gump({ exists: true });
      opens(found);
      const { loreOnce } = await loadLore({ LORE_GUMP_BUTTON: 0 });

      loreOnce(0x1234);

      expect(found.reply).toHaveBeenCalledWith(0);
    });

    it('says so once when no button is set, rather than once a read', async () => {
      opens(gump({ exists: true }));
      const { loreOnce } = await loadLore();

      loreOnce(0x1234);
      loreOnce(0x1234);

      const said = world.log.mock.calls.filter((call) =>
        String(call[0]).includes('the gump did not close'),
      );

      expect(said).toHaveLength(1);
    });
  });
});
