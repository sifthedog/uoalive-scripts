import { createTool } from '../lib/tool.js';
import {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  PICKAXE_NAME,
  SPARE_BAG_SERIAL,
} from './config.js';

const pickaxe = /* @__PURE__ */ createTool({
  label: 'pickaxe',
  name: PICKAXE_NAME,
  spareBagSerial: SPARE_BAG_SERIAL,
  held: () => player.equippedItems.oneHanded,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
});

export const isPickaxe = pickaxe.is;
export const rememberPickaxe = pickaxe.remember;

// What dig.ts watches for a tool that wore out mid-swing: a RunUO tool tracks UsesRemaining rather
// than hits, and item.hits is 0 for anything the client knows nothing about, so a serial that stops
// resolving is the only reliable evidence.
export const pickaxeSerial = pickaxe.serial;
export const equipPickaxe = pickaxe.equip;
