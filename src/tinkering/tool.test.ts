import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { TOOL_GRAPHICS } from './config.js';

const TOOL = 0x1eb8;
const TOOL_SERIAL = 0x4001;

// An OPL response as the client shapes it: properties carrying text plus substituted values
const opl = (...texts: string[]) => ({ properties: texts.map((text) => ({ text, values: [] })) });

let world: FakeWorld;

const loadTool = async () => import('./tool.js');

beforeEach(() => {
  vi.resetModules();
  world = installGlobals({
    client: {
      findObject: vi.fn(() => item({ serial: TOOL_SERIAL, graphic: TOOL })),
      queryItemOPL: vi.fn(() => undefined),
    } as never,
  });
});

describe('needsSwap', () => {
  // Tool wear is read from OPL rather than item.hits, which is 0 for anything the client knows
  // nothing about - the normal case in a pack
  it('swaps when the tool is down to its last use', async () => {
    world.client.queryItemOPL.mockReturnValue(opl('Uses Remaining: 1'));
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(true);
  });

  it('keeps a tool with uses to spare', async () => {
    world.client.queryItemOPL.mockReturnValue(opl('Uses Remaining: 40'));
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(false);
  });

  it('reads the count whatever the spacing and casing', async () => {
    const { needsSwap } = await loadTool();

    for (const text of ['uses remaining: 1', 'USES REMAINING 1', 'Uses Remaining   :   1']) {
      world.client.queryItemOPL.mockReturnValue(opl(text));
      expect(needsSwap(TOOL_SERIAL)).toBe(true);
    }
  });

  it('finds the count among other properties', async () => {
    world.client.queryItemOPL.mockReturnValue(
      opl('tinker tools', 'Weight: 1 Stone', 'Uses Remaining: 1'),
    );
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(true);
  });

  // A destroyed serial stops resolving, which is the one wear signal that works on every shard
  it('swaps when the serial no longer resolves', async () => {
    world.client.findObject.mockReturnValue(undefined);
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(true);
  });

  it('swaps when there is no tool at all', async () => {
    const { needsSwap } = await loadTool();

    expect(needsSwap(undefined)).toBe(true);
  });

  // UOAlive may not send the property. Asking again every cycle would pay the OPL timeout forever,
  // so one miss latches the question off and the break itself becomes the signal.
  it('stops asking after the first shard that does not send the property', async () => {
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(false);
    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);

    needsSwap(TOOL_SERIAL);
    needsSwap(TOOL_SERIAL);

    expect(world.client.queryItemOPL).toHaveBeenCalledTimes(1);
  });

  it('does not treat a property mentioning uses without a number as a reading', async () => {
    world.client.queryItemOPL.mockReturnValue(opl('Uses Remaining'));
    const { needsSwap } = await loadTool();

    expect(needsSwap(TOOL_SERIAL)).toBe(false);
  });
});

describe('isTool and rememberTool', () => {
  it('matches the seeded graphics with no name at all', async () => {
    const { isTool } = await loadTool();

    for (const graphic of TOOL_GRAPHICS) {
      expect(isTool(item({ serial: 1, graphic }))).toBe(true);
    }
  });

  it('matches by name when the graphic is not one of the seeded ones', async () => {
    const { isTool } = await loadTool();

    expect(isTool(item({ serial: 1, graphic: 0x9999, name: 'a tool kit' }))).toBe(true);
  });

  it('is case-insensitive about the name', async () => {
    const { isTool } = await loadTool();

    expect(isTool(item({ serial: 1, graphic: 0x9999, name: 'TOOL KIT' }))).toBe(true);
  });

  // Names are empty until the client has tooltip data, so the graphic is what survives
  it('matches by graphic once one has been seen, even with no name', async () => {
    const { isTool, rememberTool } = await loadTool();

    expect(isTool(item({ serial: 1, graphic: 0x9999 }))).toBe(false);

    rememberTool(item({ serial: 1, graphic: 0x9999, name: 'tool kit' }));

    expect(isTool(item({ serial: 2, graphic: 0x9999, name: '' }))).toBe(true);
  });

  // The first graphic wins - a later one would be a different tool, and re-learning would let a
  // stray match drag the whole run onto the wrong item
  it('keeps the first graphic it learned', async () => {
    const { isTool, rememberTool } = await loadTool();

    rememberTool(item({ serial: 1, graphic: 0x9999, name: 'tool kit' }));
    rememberTool(item({ serial: 2, graphic: 0x8888, name: 'tool kit' }));

    expect(isTool(item({ serial: 3, graphic: 0x9999 }))).toBe(true);
    expect(isTool(item({ serial: 4, graphic: 0x8888 }))).toBe(false);
  });

  it('rejects an unrelated item', async () => {
    const { isTool } = await loadTool();

    expect(isTool(item({ serial: 1, graphic: 0x1bdd, name: 'log' }))).toBe(false);
  });
});

describe('toolAlive', () => {
  it('is false for a serial that no longer resolves', async () => {
    world.client.findObject.mockReturnValue(undefined);
    const { toolAlive } = await loadTool();

    expect(toolAlive(TOOL_SERIAL)).toBe(false);
  });

  it('is false when there is no serial', async () => {
    const { toolAlive } = await loadTool();

    expect(toolAlive(undefined)).toBe(false);
  });

  it('is true while the serial resolves', async () => {
    const { toolAlive } = await loadTool();

    expect(toolAlive(TOOL_SERIAL)).toBe(true);
  });
});
