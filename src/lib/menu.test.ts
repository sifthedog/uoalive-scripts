import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

const loadMenu = async () => import('./menu.js');

const entry = (index: number, text: string) => ({
  index,
  text,
  cliloc: 0,
  hue: 0,
  replacedHue: 0,
  flags: 0,
});

const menu = (serial: number, ...items: ReturnType<typeof entry>[]) => {
  world.popupMenu.waitForContent = vi.fn(() => ({ serial, items }));
};

const choose = async (texts: string[]) => {
  const { chooseMenuEntry } = await loadMenu();

  return chooseMenuEntry({ serial: 0x1234, texts, timeoutMs: 100 });
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('chooseMenuEntry', () => {
  it('asks for the menu of the serial it was given', async () => {
    await choose(['Release']);

    expect(world.popupMenu.request).toHaveBeenCalledWith(0x1234, 100);
  });

  // A menu left open from the last object answers for that object
  it('closes whatever was open before asking', async () => {
    await choose(['Release']);

    const [closed] = world.popupMenu.close.mock.invocationCallOrder;
    const [requested] = world.popupMenu.request.mock.invocationCallOrder;

    expect(closed).toBeLessThan(requested);
  });

  it('replies to the entry whose text matches', async () => {
    menu(0x1234, entry(0, 'Add Friend'), entry(1, 'Command: Release'));

    expect(await choose(['Release'])).toBe('pressed');
    expect(world.popupMenu.reply).toHaveBeenCalledWith(1);
  });

  // The shard numbers its own entries, so a menu that omits one leaves a gap
  it('replies with the entry index, not its place in the list', async () => {
    menu(0x1234, entry(3, 'Add Friend'), entry(7, 'Release'));

    await choose(['Release']);

    expect(world.popupMenu.reply).toHaveBeenCalledWith(7);
  });

  it('matches without regard to case, and on a fragment', async () => {
    menu(0x1234, entry(0, 'COMMAND: RELEASE'));

    expect(await choose(['release'])).toBe('pressed');
  });

  it('takes the first of the texts that matches anything', async () => {
    menu(0x1234, entry(0, 'Rename'));

    expect(await choose(['Give a name', 'Rename'])).toBe('pressed');
    expect(world.popupMenu.reply).toHaveBeenCalledWith(0);
  });

  it('says noMenu when nothing came back', async () => {
    expect(await choose(['Release'])).toBe('noMenu');
    expect(world.popupMenu.reply).not.toHaveBeenCalled();
  });

  // A menu without the entry says what the object is; a menu that never came says nothing at all
  it('says noEntry, and presses nothing, when the menu has no such entry', async () => {
    menu(0x1234, entry(0, 'Add Friend'), entry(1, 'Transfer'));

    expect(await choose(['Release'])).toBe('noEntry');
    expect(world.popupMenu.reply).not.toHaveBeenCalled();
  });

  it('leaves no menu open behind a miss', async () => {
    menu(0x1234, entry(0, 'Add Friend'));

    await choose(['Release']);

    expect(world.popupMenu.close).toHaveBeenCalledTimes(2);
  });

  // The content that arrived is for something else entirely, and its indexes mean nothing here
  it('refuses a menu that belongs to another object', async () => {
    menu(0x5678, entry(0, 'Release'));

    expect(await choose(['Release'])).toBe('noMenu');
    expect(world.popupMenu.reply).not.toHaveBeenCalled();
  });
});
