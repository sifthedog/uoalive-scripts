// Which layers come off for a trance, and how long to give the moves. How it is done is
// src/lib/gear.ts. No rearm hook: nothing is ever in this character's hands.

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
  prefix: 'necro',
  layers: STRIP_LAYERS,
  moveDelayMs: STRIP_MOVE_DELAY,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
  disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
  stripAtOnce: STRIP_AT_ONCE,
});

export const { stow, stripMore, restore, survey } = gear;
