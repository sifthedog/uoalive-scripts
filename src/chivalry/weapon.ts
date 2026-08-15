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

// Only the first band needs a weapon - Consecrate Weapon enchants what is in hand - while meditation
// is refused with anything in one.
//
// ./gear.ts owns the trance round trip now, because it puts back the exact serial it took and this
// file cannot: createTool matches on graphic, deliberately, so that a weapon which broke can be
// replaced from the pack. What is left here is the draw of last resort - the trainer's answer to a
// `noWeapon` cast, and gear's fallback for a weapon that stopped resolving in the pack - plus the
// graphic latch that makes that draw match the weapon actually being trained with. Whether any of it
// is used at all is index.ts's decision, taken from what is in hand at start-up.

const weapon = /* @__PURE__ */ createWeapon({
  prefix: 'chiv',
  name: WEAPON_NAME,
  spareBagSerial: SPARE_BAG_SERIAL,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
});

export const { held, is: isWeapon, remember: rememberWeapon, rearm } = weapon;
