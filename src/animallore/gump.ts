import { LORE_GUMP_BUTTON, LORE_GUMP_TEXT } from './config.js';

// Said once: a gump that will not close is worth knowing about, and worth knowing about only once
let refused = false;

// Closed by name rather than with Gump.closeAll(), which also shuts your pack, your vendor window
// and everything else you had open.
export interface Closable {
  close: () => void;
  reply: (buttonID: number) => void;
  exists: boolean;
}

export const closeLoreGump = (gump: Closable): void => {
  gump.close();

  if (!gump.exists) {
    return;
  }

  // A gump the server sent as non-closable ignores both a right-click and the client-side close, and
  // its drawn X is a real button instead
  if (LORE_GUMP_BUTTON !== undefined) {
    gump.reply(LORE_GUMP_BUTTON);

    return;
  }

  if (!refused) {
    refused = true;
    log(
      `lore: the gump did not close - find the id its X answers to and set LORE_GUMP_BUTTON, ` +
        'or the next read may be refused with one still on screen',
    );
  }
};

// Left over from a read the loop never got to close - a refusal partway through, or a stop
export const closeStrayGump = (): void => {
  const found = Gump.findOrWait(LORE_GUMP_TEXT, 0);

  if (found) {
    closeLoreGump(found);
  }
};
