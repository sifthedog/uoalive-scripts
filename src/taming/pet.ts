import { isMobile } from '../lib/entity.js';
import { chooseMenuEntry } from '../lib/menu.js';
import { settled } from '../lib/retry.js';
import {
  KILL_CURSOR_TIMEOUT,
  KILL_MENU_TEXT,
  KILL_PICK_POLL,
  KILL_PICK_TIMEOUT,
  MENU_TIMEOUT,
  PROMPT_TIMEOUT,
  RELEASE_CONFIRM_BUTTONS,
  RELEASE_CONFIRM_POLL,
  RELEASE_CONFIRM_TEXT,
  RELEASE_CONFIRM_TIMEOUT,
  RELEASE_MENU_TEXT,
  RELEASE_POLL,
  RELEASE_TIMEOUT,
  RENAME_MENU_TEXT,
} from './config.js';

export type RenameOutcome = 'renamed' | 'noEntry' | 'noMenu' | 'noPrompt';
export type ReleaseOutcome = 'released' | 'noEntry' | 'noMenu' | 'stillPet';
export type KillOutcome = 'ordered' | 'noEntry' | 'noMenu' | 'noCursor' | 'unanswered';

// Which button the gump answers to is the same all run, so it is worked out on the first animal and
// used unquestioned after that
let confirmButton: number | undefined;

// Said once each: a shard that answers neither is worth a line, not a line per tame
let saidNoGump = false;
let saidNoButton = false;

const isPet = (serial: number): boolean => {
  const found = client.findObject(serial);

  return !!found && isMobile(found) && found.isRenamable;
};

export const renamePet = (serial: number, name: string): RenameOutcome => {
  const chosen = chooseMenuEntry({ serial, texts: RENAME_MENU_TEXT, timeoutMs: MENU_TIMEOUT });

  if (chosen !== 'pressed') {
    return chosen;
  }

  if (!prompt.waitUntilOpen(PROMPT_TIMEOUT)) {
    return 'noPrompt';
  }

  prompt.reply(name);

  return 'renamed';
};

// Both Gump.last and Gump.findOrWait answer with one of these, the way lib's Closable does
interface Confirmable {
  exists: boolean;
  hasButton: (id: number) => boolean;
  reply: (buttonID: number) => void;
  close: () => void;
}

// Identified as whatever the server sent after the entry was pressed rather than by its wording,
// which is localised. Nothing else in a taming cycle opens a gump.
const findConfirm = (before: number): Confirmable | undefined => {
  settled({
    timeoutMs: RELEASE_CONFIRM_TIMEOUT,
    pollMs: RELEASE_CONFIRM_POLL,
    landed: () => Gump.lastSerial !== before,
  });

  // Taken whether or not the serial moved: a client that does not track it still has the gump
  const last = Gump.last;

  if (last?.exists) {
    return last;
  }

  for (const text of RELEASE_CONFIRM_TEXT) {
    const found = Gump.findOrWait(text, RELEASE_CONFIRM_POLL);

    if (found) {
      return found;
    }
  }

  return undefined;
};

const answerConfirm = (before: number, button: number): void => {
  const gump = findConfirm(before);

  if (!gump) {
    if (!saidNoGump) {
      saidNoGump = true;
      log(
        `tame: found no gump to confirm the release with - lastSerial ${before} -> ` +
          `${Gump.lastSerial}, last ${Gump.last ? `exists ${Gump.last.exists}` : 'null'}`,
      );
    }

    return;
  }

  if (!gump.hasButton(button) && !saidNoButton) {
    saidNoButton = true;
    log(`tame: the release gump does not admit to a button ${button} - pressing it anyway`);
  }

  gump.reply(button);
};

export const releasePet = (serial: number): ReleaseOutcome => {
  const buttons = confirmButton === undefined ? RELEASE_CONFIRM_BUTTONS : [confirmButton];
  let pressed = false;

  for (const button of buttons) {
    const before = Gump.lastSerial;
    const chosen = chooseMenuEntry({ serial, texts: RELEASE_MENU_TEXT, timeoutMs: MENU_TIMEOUT });

    // Better proof than the flag, and free: the entry is on the menu only while it is your pet, so
    // one that has gone since the last press means the press worked
    if (chosen === 'noEntry' && pressed) {
      return 'released';
    }

    if (chosen !== 'pressed') {
      return pressed ? 'stillPet' : chosen;
    }

    pressed = true;
    answerConfirm(before, button);

    const gone = settled({
      timeoutMs: RELEASE_TIMEOUT,
      pollMs: RELEASE_POLL,
      landed: () => !isPet(serial),
    });

    if (gone) {
      if (confirmButton === undefined) {
        confirmButton = button;
        log(`tame: the release gump answers to button ${button}`);
      }

      return 'released';
    }
  }

  // A confirmation nobody answered is modal on some clients, and would refuse the context menu of
  // every animal after this one
  if (Gump.last?.exists) {
    Gump.last.close();
  }

  return 'stillPet';
};

// The cursor the shard raises is left for the player to answer - nothing here targets anything, so
// what the pet attacks is always a human decision
export const commandKill = (serial: number, name: string): KillOutcome => {
  // Or target.wait below answers for whatever cursor was already up
  if (target.open) {
    target.cancel();
  }

  const chosen = chooseMenuEntry({ serial, texts: KILL_MENU_TEXT, timeoutMs: MENU_TIMEOUT });

  if (chosen !== 'pressed') {
    return chosen;
  }

  if (!target.wait(KILL_CURSOR_TIMEOUT)) {
    return 'noCursor';
  }

  log(`tame: told '${name}' to kill - pick its target`);

  const picked = settled({
    timeoutMs: KILL_PICK_TIMEOUT,
    pollMs: KILL_PICK_POLL,
    landed: () => !target.open,
  });

  return picked ? 'ordered' : 'unanswered';
};
