// Which layers come off for a trance, and how long to give the moves. How it is done is
// src/lib/gear.ts.
//
// This owns the hands, where ./weapon.ts used to: gear puts back the exact serial it took, so a
// weapon with properties comes back as itself. weapon.ts's draw stays underneath as the fallback for
// the one case a serial cannot answer - the weapon broke while it sat in the pack.

import { createGear } from '../lib/gear.js';
import {
  DISARM_ATTEMPTS,
  DISARM_POLL,
  DISARM_TIMEOUT,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  STRIP_AT_ONCE,
  STRIP_LAYERS,
  STRIP_MOVE_DELAY,
} from './config.js';
import { rearm } from './weapon.js';

const gear = /* @__PURE__ */ createGear({
  prefix: 'train',
  layers: STRIP_LAYERS,
  moveDelayMs: STRIP_MOVE_DELAY,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
  stripAtOnce: STRIP_AT_ONCE,
  rearm,
});

export const { stow, stripMore, restore, survey } = gear;
