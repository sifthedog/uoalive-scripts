import { PACK_LIMIT } from './config.js';

// Anything here ends the run cleanly; the loop asks before every swing. There is no box check:
// mining roams, and the one this folder started with was lumberjacking's forest, which stopped
// every run on cycle zero before it had scanned, equipped or swung at anything.
//
// There is no weight check either, and that is not an oversight. Being over the limit is what
// triggers the smelt, so a guard that stopped the run at a buffer below it would fire first, every
// time, and the smelt would never happen at all. The loop stops on weight itself - but only after
// smelting has had its turn and failed to free anything.
export const stopReason = () => {
  if (player.isDead) {
    return 'you are dead';
  }

  const top = (player.backpack?.contents ?? []).length;
  if (top >= PACK_LIMIT) {
    return `pack is full (${top} items at the top level)`;
  }

  return undefined;
};
