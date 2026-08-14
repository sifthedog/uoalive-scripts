import { overweight } from '../lib/weight.js';
import { PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// Anything here ends the run cleanly; the loop asks before every craft
export const stopReason = () => {
  if (player.isDead) {
    return 'you are dead';
  }

  // Buffer, so the stop lands before the shard starts refusing to move the new item
  if (overweight(WEIGHT_BUFFER)) {
    return `overweight (${player.weight}/${player.weightMax})`;
  }

  // Rings do not stack, so a long ring phase hits the container item cap before the weight cap
  const top = (player.backpack?.contents ?? []).length;
  if (top >= PACK_LIMIT) {
    return `pack is full (${top} items at the top level)`;
  }

  return undefined;
};
