// The tiledata bits getTerrainList and getStatic answer with. The vendored typings hand `flags` back
// as a bare number with no enum to read it by, so these are the stock RunUO/ClassicUO values and a
// hypothesis about this shard - on the same footing as mining's ORE_TILE_GRAPHICS.
//
// Never normalise flags with >>> 0: the high tiledata bits can arrive as a negative int32, and every
// mask here is small enough that `&` reads it correctly either way.
export const WALL = 0x10;
export const IMPASSABLE = 0x40;
export const WET = 0x80; // water: passable by the flags, not on foot
export const SURFACE = 0x200;
export const BRIDGE = 0x400; // stairs and ramps, which are stood on like a surface

// What a flag set means, for the survey a dead-end run prints. A mountainside that comes back
// without 'impassable' beside it is what says these numbers are wrong for this shard.
export const describeFlags = (flags: number): string => {
  const named = [
    [IMPASSABLE, 'impassable'],
    [WET, 'wet'],
    [SURFACE, 'surface'],
    [BRIDGE, 'bridge'],
    [WALL, 'wall'],
  ] as const;

  const set = named.filter(([bit]) => (flags & bit) !== 0).map(([, name]) => name);

  return set.length > 0 ? set.join(' ') : '-';
};
