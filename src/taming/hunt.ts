import { distanceTo, nameOf } from '../lib/entity.js';
import { queryOPL } from '../lib/opl.js';
import { HUNT_RADIUS, OPL_TIMEOUT, PET_NAME } from './config.js';

export interface Quarry {
  serial: number;
  name: string;
  graphic: number;
}

export interface Hunt {
  quarry: Quarry;
  inSight: number;
}

// Reset by re-pasting the script, which is the whole of what 'for the session' means here
const skipped = new Set<number>();

export const leaveOut = (serial: number): void => {
  skipped.add(serial);
};

const mine = (name: string): boolean =>
  PET_NAME !== '' && name.toLowerCase() === PET_NAME.toLowerCase();

// Names read empty until the client has tooltip data, so the one about to be taken is asked for by
// tooltip rather than every candidate on every scan
const named = (mobile: Mobile): string => {
  if (mobile.name) {
    return mobile.name;
  }

  return (queryOPL(mobile.serial, OPL_TIMEOUT, 'tame')?.name ?? '').trim() || nameOf(mobile);
};

export const nextQuarry = (graphic: number): Hunt | undefined => {
  if (HUNT_RADIUS <= 0) {
    return undefined;
  }

  const candidates = client
    // null hue: the same body in any colour is the same type of animal
    .findAllMobilesOfType(graphic, null, null, null, HUNT_RADIUS)
    .filter(
      (mobile) =>
        // graphic reads 0 for an entity the client is no longer tracking
        mobile.graphic !== 0 &&
        !skipped.has(mobile.serial) &&
        !mobile.isDead &&
        // True for pets and followers, so this is every animal the run has already kept
        !mobile.isRenamable &&
        // Measured rather than left to the scan's own range, whose meaning next to these arguments
        // is undocumented, where distanceTo is the Chebyshev the shard measures reach in
        distanceTo(mobile) <= HUNT_RADIUS &&
        !mine(mobile.name),
    )
    .sort((a, b) => distanceTo(a) - distanceTo(b));

  for (const mobile of candidates) {
    const name = named(mobile);

    // Released under the name rather than kept, so nothing but the name says it was ever yours
    if (mine(name)) {
      leaveOut(mobile.serial);
      continue;
    }

    return {
      quarry: { serial: mobile.serial, name, graphic: mobile.graphic },
      inSight: candidates.length,
    };
  }

  return undefined;
};
