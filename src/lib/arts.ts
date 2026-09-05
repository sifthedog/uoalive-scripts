// Graphics for items more than one script has to recognise, so two folders cannot disagree about the
// same object - which two of them once did about iron ingots, each shipping its own set.

// An ingot stack's graphic changes with its size, so this is the four stack-size arts as a
// contiguous range. Nothing here is load-bearing - the real graphic is learned by diffing the pack
// across the first successful smelt - and mining's own copy used to carry 0x1bee in place of 0x1bf0,
// which is off the end of the run.
export const INGOT_GRAPHICS = new Set([0x1bef, 0x1bf0, 0x1bf1, 0x1bf2]);

// Every corpse in the game is this art; what died is carried in the hue and the name.
export const CORPSE_GRAPHIC = 0x2006;
