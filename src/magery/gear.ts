// Which layers come off for a trance, and how long to give the moves. How it is done is
// src/lib/gear.ts.
//
// This run holds nothing, so the strip is about the armour, and there is no rearm hook because there
// is no weapon to fall back on drawing.

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

const gear = /* @__PURE__ */ createGear({
  prefix: 'mage',
  layers: STRIP_LAYERS,
  moveDelayMs: STRIP_MOVE_DELAY,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
  stripAtOnce: STRIP_AT_ONCE,
});

export const { stow, stripMore, restore, survey } = gear;
