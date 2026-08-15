import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

// This script has no stall watchdog - see config.ts for why - so the heartbeat is the only thing
// standing between a long trance and a run that looks hung.
export const heartbeat = /* @__PURE__ */ createHeartbeat({
  prefix: 'necro',
  noun: 'casts',
  everyMs: HEARTBEAT_EVERY,
});

export const { beat, resetBeat } = heartbeat;
