import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

export const heartbeat = /* @__PURE__ */ createHeartbeat({
  prefix: 'sweep',
  noun: 'stacks picked up',
  everyMs: HEARTBEAT_EVERY,
});

export const { beat, resetBeat } = heartbeat;
