// Graphics for items more than one script has to recognise. A folder's own config.ts is the place
// for anything only it cares about; this is for the arts where two of them would otherwise disagree
// about the same object - which mining and tinkering already did about iron ingots.

// An ingot stack's graphic changes with its size the way an ore pile's does, so this is the four
// stack-size arts as a contiguous range rather than one graphic. Tinkering matches against it with
// hue 0 pinned - coloured ores keep their own hue; mining only reads it to avoid re-logging an art
// it has already learned. Mining's copy of this used to carry 0x1bee in place of 0x1bf0, which is
// off the end of the run; nothing depended on it, but two scripts naming the same item differently
// is a fault waiting for the first one that does.
export const INGOT_GRAPHICS = new Set([0x1bef, 0x1bf0, 0x1bf1, 0x1bf2]);
