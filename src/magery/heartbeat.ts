import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

// This script has no stall watchdog - see config.ts for why - so the heartbeat is the only thing
// standing between a long trance and a run that looks hung. At 50 mana a cast the last band is the
// quietest thing in the repo.
export const heartbeat = /* @__PURE__ */ createHeartbeat({
  prefix: 'mage',
  noun: 'casts',
  everyMs: HEARTBEAT_EVERY,
});

export const { beat, resetBeat } = heartbeat;
