import { GUMP_POLL, GUMP_SERIAL, GUMP_TIMEOUT } from './config.js';

// The client reports serials as signed 32-bit ints but takes them either way, so try both forms
// rather than depending on which convention a given call happens to use.
const SERIALS = GUMP_SERIAL === undefined ? [] : [...new Set([GUMP_SERIAL >>> 0, GUMP_SERIAL | 0])];

export const craftGump = (): Gump | undefined => {
  for (const serial of SERIALS) {
    if (Gump.exists(serial)) {
      const found = Gump.findOrWait(serial, GUMP_POLL);
      if (found) {
        return found;
      }
    }
  }

  // Gump.last is `Gump | null`, so normalise to undefined for the ?? and ?. chains downstream.
  // It is the fallback rather than the primary: on UOAlive it goes null while the gump is open.
  const last = Gump.last;
  return last && last.exists ? last : undefined;
};

// A gump's layout cannot be read, and the craft gump keeps the same serial across its pages, so
// pages are told apart by which buttons they carry rather than by text or by a serial change.
export const pageWith = (buttonID: number, timeout: number): Gump | undefined => {
  for (let waited = 0; waited <= timeout; waited += GUMP_POLL) {
    const gump = craftGump();
    if (gump && gump.hasButton(buttonID)) {
      return gump;
    }
    sleep(GUMP_POLL);
  }

  return undefined;
};

export const openCraftGump = (toolSerial: number, categoryButton: number): Gump | undefined => {
  const alreadyOpen = pageWith(categoryButton, 0);
  if (alreadyOpen) {
    return alreadyOpen;
  }

  player.use(toolSerial);
  return pageWith(categoryButton, GUMP_TIMEOUT);
};

// Backing out closes and reopens rather than pressing a button: an unidentified button might
// craft something, while using the tool again always brings back a fresh category page.
export const backToCategories = (
  toolSerial: number,
  categoryButton: number,
): Gump | undefined => {
  craftGump()?.close();
  sleep(GUMP_POLL);
  return openCraftGump(toolSerial, categoryButton);
};
