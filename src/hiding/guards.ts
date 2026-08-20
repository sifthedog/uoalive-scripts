import { dead, firstReason } from '../lib/guards.js';

// No threat watch: player.say reveals a hidden character, so calling the guards would undo the very
// thing this run is training. Nothing goes in the pack either, so weight and slots do not apply.
export const stopReason = (): string | undefined => firstReason(dead);
