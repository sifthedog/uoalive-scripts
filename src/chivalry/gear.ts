// Which layers come off for a trance, and how long to give the moves. How it is done is
// src/lib/gear.ts.
//
// Unconditional, where the weapon half of this folder is not: gear only puts back what it took, so a
// paladin who started empty-handed never tries. That is what lets an unarmed but armoured character
// be undressed for the trance, which the weapon-only version could not do.

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
  prefix: 'chiv',
  layers: STRIP_LAYERS,
  moveDelayMs: STRIP_MOVE_DELAY,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
  stripAtOnce: STRIP_AT_ONCE,
  rearm,
});

export const { stow, stripMore, restore, survey } = gear;
