// Graphics for items more than one script has to recognise. A folder's own config.ts is the place
// for anything only it cares about; this is for the arts where two of them would otherwise disagree
// about the same object - which two scripts once did about iron ingots, each shipping its own set
// for the same item. Mining is the only reader left, and this stays here rather than moving into
// its config because the disagreement is the point.

// An ingot stack's graphic changes with its size the way an ore pile's does, so this is the four
// stack-size arts as a contiguous range rather than one graphic. Mining only reads it to avoid
// re-logging an art it has already learned, so nothing here is load-bearing: the real graphic is
// learned by diffing the pack across the first successful smelt. Mining's own copy used to carry
// 0x1bee in place of 0x1bf0, which is off the end of the run.
export const INGOT_GRAPHICS = new Set([0x1bef, 0x1bf0, 0x1bf1, 0x1bf2]);
