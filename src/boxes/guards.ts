import { dead, firstReason, heavy, packFull, type Guard } from '../lib/guards.js';
import { DROP_KEYS, PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// The weight and pack-slot checks are wrong here unless the keys are being kept: emptying a box
// moves what is in it onto the floor, which frees weight and a slot rather than costing either. Left
// in unconditionally they stop the run before the first box on exactly the overloaded character it
// would have relieved - which is what "15 wooden boxes, emptied 0" turned out to be.
const whenKeepingKeys =
  (guard: Guard): Guard =>
  () => {
    if (DROP_KEYS) {
      return undefined;
    }

    const reason = guard();

    return reason && `${reason} and keys are going into the pack`;
  };

// Asked before every box; the loop reports whatever this says.
export const stopReason = (): string | undefined =>
  firstReason(
    dead,
    whenKeepingKeys(heavy(WEIGHT_BUFFER)),
    whenKeepingKeys(packFull(PACK_LIMIT)),
  );
