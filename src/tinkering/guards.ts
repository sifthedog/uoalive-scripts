import { dead, firstReason, heavy, packFull } from '../lib/guards.js';
import { PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// Anything here ends the run cleanly; the loop asks before every craft. Rings do not stack, so a
// long ring phase hits the container item cap before the weight cap.
export const stopReason = (): string | undefined =>
  firstReason(dead, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));
