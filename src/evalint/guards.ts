import { dead, firstReason } from '../lib/guards.js';

// No weight or pack-slot check: evaluating puts nothing in the pack.
export const stopReason = (): string | undefined => firstReason(dead);
