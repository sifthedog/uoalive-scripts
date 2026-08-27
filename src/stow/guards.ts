import { dead, firstReason } from '../lib/guards.js';

// dead alone: this script is the relief a weight guard would stop, and with the destination inside
// the pack it does not change the weight at all
export const stopReason = (): string | undefined => firstReason(dead);
