import { dead, firstReason } from '../lib/guards.js';

// Anything here ends the run cleanly; the loop asks before every cast, and the mana wait asks on
// every poll - which is the one that matters, because a trance is where this script spends most of
// its time and a character can be killed in the middle of one.
//
// There is no weight check: a trainer picks nothing up. There is no pack check either, for the same
// reason - the only thing that moves into the pack all run is the weapon it stowed itself.
export const stopReason = (): string | undefined => firstReason(dead);
