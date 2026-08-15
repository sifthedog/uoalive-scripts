import { createWeapon } from '../lib/weapon.js';
import {
  DISARM_ATTEMPTS,
  DISARM_POLL,
  DISARM_TIMEOUT,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  SPARE_BAG_SERIAL,
  WEAPON_NAME,
} from './config.js';

// These are weapon abilities and are refused with an empty hand, while meditation is refused with
// anything in one - so the weapon goes to the pack for the trance and comes back for the casting.
//
// ./gear.ts owns that round trip now, because it puts back the exact serial it took and this file
// cannot: createTool matches on graphic, deliberately, so that a weapon which broke can be replaced
// from the pack. What is left here is the draw of last resort - the trainer's answer to a `noWeapon`
// cast, and gear's fallback for a weapon that stopped resolving while it sat in the pack - plus the
// graphic latch that makes that draw match the weapon actually being trained with.

const weapon = /* @__PURE__ */ createWeapon({
  prefix: 'train',
  name: WEAPON_NAME,
  spareBagSerial: SPARE_BAG_SERIAL,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
});

export const { held, is: isWeapon, remember: rememberWeapon, rearm } = weapon;
