import { dead, firstReason, heavy, packFull } from '../lib/guards.js';
import { PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

export const stopReason = (): string | undefined =>
  firstReason(dead, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));
