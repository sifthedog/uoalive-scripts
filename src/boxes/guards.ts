import { DROP_KEYS, PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// Anything here ends the emptying pass; the loop asks before every box and reports what it said.
//
// The weight and pack-slot checks are inherited from the crafting scripts, where every cycle *adds*
// to the pack, and they are wrong here unless the keys are being kept: emptying a box moves what is
// in it onto the floor, which frees weight and a pack slot rather than costing either. Left in
// unconditionally they stop the run before the first box on exactly the overloaded character the
// run would have relieved - which is what "15 wooden boxes, emptied 0" turned out to be.
export const stopReason = (): string | undefined => {
  if (player.isDead) {
    return 'you are dead';
  }

  if (!DROP_KEYS) {
    // Buffer, so the stop lands before the shard starts refusing to move the new item
    if (player.weight > player.weightMax - WEIGHT_BUFFER) {
      return `overweight (${player.weight}/${player.weightMax}) and keys are going into the pack`;
    }

    const top = (player.backpack?.contents ?? []).length;
    if (top >= PACK_LIMIT) {
      return `pack is full (${top} items at the top level) and keys are going into the pack`;
    }
  }

  return undefined;
};
