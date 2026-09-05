import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, mobile, type FakeWorld } from '../test-support/uo.js';
import { RELEASE_CONFIRM_BUTTONS } from './config.js';

let world: FakeWorld;

const loadPet = async () => import('./pet.js');

const menu = (...texts: string[]) => {
  world.popupMenu.waitForContent = vi.fn(() => ({
    serial: 0x1234,
    items: texts.map((text, index) => ({
      index,
      text,
      cliloc: 0,
      hue: 0,
      replacedHue: 0,
      flags: 0,
    })),
  }));
};

// The menu goes away with the pet, which is how the shard says the release went through
const menuLosesReleaseAfter = (presses: number) => {
  let left = presses;

  world.popupMenu.waitForContent = vi.fn(() => ({
    serial: 0x1234,
    items: (left > 0 ? ['Release'] : ['Add Friend']).map((text, index) => ({
      index,
      text,
      cliloc: 0,
      hue: 0,
      replacedHue: 0,
      flags: 0,
    })),
  }));

  world.popupMenu.reply = vi.fn(() => {
    left--;
  });
};

// The server sends the confirmation in answer to the entry being pressed, so the serial only moves
// once something has been pressed
const sends = (options: { has?: number[]; yes?: number }) => {
  const confirm = {
    hasButton: vi.fn((id: number) => (options.has ?? []).includes(id)),
    reply: vi.fn((id: number) => {
      if (id === options.yes) {
        world.client.findObject.mockReturnValue(
          mobile({ serial: 0x1234, graphic: 0x00d0, isRenamable: false }),
        );
      }
    }),
    exists: true,
    close: vi.fn(),
  };

  world.client.findObject.mockReturnValue(
    mobile({ serial: 0x1234, graphic: 0x00d0, isRenamable: true }),
  );

  world.popupMenu.reply = vi.fn(() => {
    world.gump.lastSerial += 1;
    world.gump.last = confirm;
  });

  return confirm;
};

const pet = (isRenamable: boolean) => {
  world.client.findObject.mockReturnValue(mobile({ serial: 0x1234, graphic: 0x00d0, isRenamable }));
};

// The flag flips a poll or two after the menu entry is pressed, which is what settled() is waiting on
const petUntil = (polls: number) => {
  let left = polls;

  world.client.findObject.mockImplementation(() =>
    mobile({ serial: 0x1234, graphic: 0x00d0, isRenamable: left-- > 0 }),
  );
};

beforeEach(() => {
  vi.resetModules();
  world = installGlobals();
});

describe('renamePet', () => {
  it('presses the rename entry and answers the prompt with the name', async () => {
    menu('Add Friend', 'Rename');
    world.prompt.waitUntilOpen = vi.fn(() => true);
    const { renamePet } = await loadPet();

    expect(renamePet(0x1234, 'sifinha')).toBe('renamed');
    expect(world.popupMenu.reply).toHaveBeenCalledWith(1);
    expect(world.prompt.reply).toHaveBeenCalledWith('sifinha');
  });

  it('says noEntry when the menu came without a rename on it', async () => {
    menu('Add Friend', 'Transfer');
    const { renamePet } = await loadPet();

    expect(renamePet(0x1234, 'sifinha')).toBe('noEntry');
    expect(world.prompt.reply).not.toHaveBeenCalled();
  });

  it('says noMenu when no menu came at all', async () => {
    const { renamePet } = await loadPet();

    expect(renamePet(0x1234, 'sifinha')).toBe('noMenu');
  });

  // Nothing is said into a chat box that is not asking, which would land in public speech
  it('says noPrompt, and says nothing at all, when no prompt opens', async () => {
    menu('Rename');
    const { renamePet } = await loadPet();

    expect(renamePet(0x1234, 'sifinha')).toBe('noPrompt');
    expect(world.prompt.reply).not.toHaveBeenCalled();
  });
});

describe('releasePet', () => {
  it('presses the release entry and reads the flag going out as the proof', async () => {
    menu('Command: Release');
    petUntil(1);
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
    expect(world.popupMenu.reply).toHaveBeenCalledWith(0);
  });

  it('says noEntry when the menu came without a release on it', async () => {
    menu('Add Friend');
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('noEntry');
  });

  it('says noMenu when no menu came at all', async () => {
    pet(true);
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('noMenu');
  });

  it('answers the gump the server sent after the entry was pressed', async () => {
    const confirm = sends({ has: [1], yes: 1 });
    menu('Release');
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
    expect(confirm.reply).toHaveBeenCalledWith(1);
  });

  // The point of the candidate list: a first press that turns out to be Cancel is not the end of it
  it('works its way through the candidates until the pet is let go', async () => {
    const confirm = sends({ has: [0, 1, 2], yes: 2 });
    menu('Release');
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
    expect(confirm.reply.mock.calls.map(([id]) => id)).toEqual([1, 2]);
  });

  it('presses a candidate the gump does not admit to rather than give up on it', async () => {
    const confirm = sends({ has: [], yes: 1 });
    menu('Release');
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
    expect(confirm.reply).toHaveBeenCalledWith(RELEASE_CONFIRM_BUTTONS[0]);
  });

  // Worked out once and used unquestioned after that, so the second animal costs one press
  it('remembers the button that worked for the rest of the run', async () => {
    const confirm = sends({ has: [0, 1, 2], yes: 2 });
    menu('Release');
    const { releasePet } = await loadPet();

    releasePet(0x1234);
    confirm.reply.mockClear();
    releasePet(0x1234);

    expect(confirm.reply.mock.calls.map(([id]) => id)).toEqual([2]);
  });

  // isRenamable is the client's flag and it does not always refresh; the menu is the shard's own word
  it('takes the release entry having gone as proof, whatever the flag still says', async () => {
    menuLosesReleaseAfter(1);
    pet(true);
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
  });

  it('says stillPet when every candidate has been tried and it is yours', async () => {
    sends({ has: [0, 1, 2] });
    menu('Release');
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('stillPet');
    expect(world.popupMenu.reply).toHaveBeenCalledTimes(RELEASE_CONFIRM_BUTTONS.length);
  });

  it('does not need a confirmation gump to call it released', async () => {
    menu('Release');
    petUntil(1);
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('released');
  });

  // A client that does not move Gump.lastSerial still has the gump, and it is still the one to press
  it('takes the gump on screen even when the serial never moved', async () => {
    const confirm = { hasButton: vi.fn(() => true), reply: vi.fn(), exists: true, close: vi.fn() };

    menu('Release');
    pet(true);
    world.gump.last = confirm;
    world.popupMenu.reply = vi.fn();
    const { releasePet } = await loadPet();

    releasePet(0x1234);

    expect(confirm.reply).toHaveBeenCalledWith(1);
  });

  it('falls back to finding the gump by its wording', async () => {
    const confirm = { hasButton: vi.fn(() => true), reply: vi.fn(), exists: true, close: vi.fn() };

    menu('Release');
    pet(true);
    world.gump.findOrWait = vi.fn(() => confirm);
    world.popupMenu.reply = vi.fn();
    const { releasePet } = await loadPet();

    releasePet(0x1234);

    expect(confirm.reply).toHaveBeenCalledWith(1);
  });

  // Modal on some clients, and it would refuse the context menu of every animal after this one
  it('closes a confirmation it could not answer before giving up', async () => {
    const confirm = { hasButton: vi.fn(() => true), reply: vi.fn(), exists: true, close: vi.fn() };

    menu('Release');
    pet(true);
    world.gump.last = confirm;
    const { releasePet } = await loadPet();

    expect(releasePet(0x1234)).toBe('stillPet');
    expect(confirm.close).toHaveBeenCalled();
  });
});

describe('commandKill', () => {
  // The cursor is the player's to answer: what the pet attacks is never the script's decision
  it('presses the kill entry and leaves the cursor alone', async () => {
    menu('Command: Kill');
    world.target.wait = vi.fn(() => true);
    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('ordered');
    expect(world.popupMenu.reply).toHaveBeenCalledWith(0);
    expect(world.target.entity).not.toHaveBeenCalled();
    expect(world.target.waitTargetEntity).not.toHaveBeenCalled();
  });

  // Or target.wait would answer for whatever cursor was already up
  it('cancels a live cursor before giving the order, and only a live one', async () => {
    menu('Kill');
    world.target.wait = vi.fn(() => true);
    const { commandKill } = await loadPet();

    commandKill(0x1234, 'sifinha');
    expect(world.target.cancel).not.toHaveBeenCalled();

    world.target.open = true;
    commandKill(0x1234, 'sifinha');
    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('says noCursor when the order raised nothing to click with', async () => {
    menu('Kill');
    world.target.wait = vi.fn(() => false);
    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('noCursor');
  });

  // Up for a few polls, then answered, which is what a person clicking looks like from in here
  it('waits for the cursor to be answered before it says the order landed', async () => {
    let up = 3;

    menu('Kill');
    world.target.wait = vi.fn(() => true);

    Object.defineProperty(world.target, 'open', {
      configurable: true,
      get: () => up-- > 0,
    });

    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('ordered');
  });

  it('says unanswered when the cursor is still up at the end of the wait', async () => {
    menu('Kill');
    world.target.wait = vi.fn(() => true);
    world.target.open = true;
    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('unanswered');
  });

  it('says noEntry when the menu came without a kill on it', async () => {
    menu('Add Friend');
    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('noEntry');
  });

  it('says noMenu when no menu came at all', async () => {
    const { commandKill } = await loadPet();

    expect(commandKill(0x1234, 'sifinha')).toBe('noMenu');
  });
});
