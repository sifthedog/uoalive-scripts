import { dead, firstReason } from '../lib/guards.js';

// No weight or pack-slot check: reading a creature puts nothing in the pack.
export const stopReason = (): string | undefined => firstReason(dead);
