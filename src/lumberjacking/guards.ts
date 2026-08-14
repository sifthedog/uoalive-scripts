import { overweight } from '../lib/weight.js';
import { describeBounds, inBounds } from './bounds.js';
import { PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// Anything here ends the run cleanly; the loop asks before every chop
export const stopReason = () => {
  if (player.isDead) {
    return 'you are dead';
  }

  // Every step is checked before it is taken, so this only trips if something else moved the
  // character - a teleporter, a boat, a GM - or if the run started outside the box
  if (!inBounds(player.x, player.y)) {
    return `at ${player.x},${player.y}, outside ${describeBounds()}`;
  }

  // Buffer, so the stop lands before the shard starts refusing to move the new logs
  if (overweight(WEIGHT_BUFFER)) {
    return `overweight (${player.weight}/${player.weightMax})`;
  }

  const top = (player.backpack?.contents ?? []).length;
  if (top >= PACK_LIMIT) {
    return `pack is full (${top} items at the top level)`;
  }

  return undefined;
};
