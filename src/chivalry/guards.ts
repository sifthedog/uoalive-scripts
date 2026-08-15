import { dead, firstReason, hurt } from '../lib/guards.js';
import { HURT_FLOOR } from './config.js';

// One floor, asked two ways: below it the run bandages itself (heal.ts), and still below it once the
// bandaging is done the guard ends the run.
const floor = /* @__PURE__ */ hurt(HURT_FLOOR);

export const belowFloor = (): boolean => floor() !== undefined;

// Asked before every cast and on every poll of the mana wait - the poll being the one that matters,
// because a trance is where this script spends most of its time.
//
// The health floor is here for Noble Sacrifice, which sets the caster's hit points to 1 where it
// finds anything to heal. A backstop rather than the first line: the loop bandages first.
//
// No weight or pack check: a paladin picks nothing up, and the only thing that moves into the pack
// all run is the weapon it stowed itself.
export const stopReason = (): string | undefined => firstReason(dead, floor);
