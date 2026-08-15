import { dead, firstReason } from '../lib/guards.js';

// Asked before every cast and on every poll of the mana wait - the poll being the one that matters,
// because a trance is where this script spends most of its time.
//
// No weight or pack check: the only thing that moves into the pack all run is the weapon it stowed
// itself.
export const stopReason = (): string | undefined => firstReason(dead);
