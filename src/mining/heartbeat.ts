import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

export const { beat, resetBeat } = createHeartbeat({
  prefix: 'mining',
  noun: 'swings',
  everyMs: HEARTBEAT_EVERY,
});
