import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

export const heartbeat = /* @__PURE__ */ createHeartbeat({
  prefix: 'mining',
  noun: 'swings',
  everyMs: HEARTBEAT_EVERY,
});

export const { beat, resetBeat } = heartbeat;
