import { dead, firstReason } from '../lib/guards.js';

// Asked before every cast and on every poll of the mana wait - the poll being the one that matters,
// because a trance is where this script spends most of its time.
//
// No health floor, unlike src/necromancy/ and src/chivalry/: nothing in this table hurts the caster,
// so the only thing that can take the run's health is something that wandered up - and stopping is
// the whole plan for that either way. No weight or pack check either: nothing is picked up.
export const stopReason = (): string | undefined => firstReason(dead);
