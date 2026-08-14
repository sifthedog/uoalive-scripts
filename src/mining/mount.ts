import { untilLanded } from '../lib/retry.js';
import { DISMOUNT_ATTEMPTS, DISMOUNT_POLL, DISMOUNT_TIMEOUT } from './config.js';

// Riding breaks both halves of this script at once: most shards refuse the swing outright to a
// mounted character, and the fire beetle you are sitting on is not a beetle you can target as a
// forge. Since the beetle is both the ride there and the smelter once you arrive, getting off it
// is a step, not a precondition - so the loop asks every cycle rather than once at the start, and
// a remount mid-run costs one cycle instead of the rest of the session.

let reported = false;

export const dismount = (): boolean => {
  if (!player.equippedItems.mount) {
    return true;
  }

  if (!reported) {
    log('mount: getting off before working');
    reported = true;
  }

  // A cursor left open by the last swing would swallow the double-click
  target.cancel();

  const off = untilLanded({
    label: 'dismount',
    attempts: DISMOUNT_ATTEMPTS,
    timeoutMs: DISMOUNT_TIMEOUT,
    pollMs: DISMOUNT_POLL,

    // Double-clicking yourself is how you get off; there is no dismount call in this API
    act: () => player.use(player.serial),

    // The mount layer clearing is the proof
    landed: () => !player.equippedItems.mount,
  });

  if (off) {
    reported = false;
  }

  return off;
};
