import { createHeartbeat } from '../lib/heartbeat.js';
import { HEARTBEAT_EVERY } from './config.js';

export const { beat, resetBeat } = createHeartbeat({
  prefix: 'lumberjack',
  noun: 'chops',
  everyMs: HEARTBEAT_EVERY,
});
