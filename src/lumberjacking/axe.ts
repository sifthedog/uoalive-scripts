import { createTool } from '../lib/tool.js';
import {
  AXE_NAME,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  SPARE_BAG_SERIAL,
} from './config.js';

const axe = /* @__PURE__ */ createTool({
  label: 'axe',
  name: AXE_NAME,
  spareBagSerial: SPARE_BAG_SERIAL,

  // Axes are two-handed, hatchets are one-handed, and either will chop
  held: () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded,

  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
});

export const isAxe = axe.is;
export const rememberAxe = axe.remember;

// The serial the chop is swung with, so a worn-out axe can be spotted by it no longer resolving
export const axeSerial = axe.serial;
export const equipAxe = axe.equip;
