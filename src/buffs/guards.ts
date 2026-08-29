import { dead, firstReason } from '../lib/guards.js';

// Death only: whoever runs this is in a fight, nothing goes in the pack, and a health floor would
// stop the keeper exactly when the buffs are worth most.
export const stopReason = (): string | undefined => firstReason(dead);
