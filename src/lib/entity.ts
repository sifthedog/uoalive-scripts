// Serials come back as signed 32-bit ints, so an unshifted one prints as 0x-3266af2f
export const hex = (value: number): string => `0x${(value >>> 0).toString(16)}`;

// Chebyshev, because a diagonal step covers a tile of x and a tile of y at once - so a tile two
// away diagonally is two steps, the same as two away in a straight line.
export const distanceTo = (spot: { x: number; y: number }): number =>
  Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));

// _tag is how the client's own typings tell an Item from a Mobile, and it costs no round trip
export const isMobile = (entity: Item | Mobile): entity is Mobile => entity._tag === 'Mobile';

// Names are empty until the client has tooltip data, so a serial is the fallback that always works
export const nameOf = (entity: { name?: string; serial: number }): string =>
  entity.name ?? hex(entity.serial);

// Walk to a mobile, re-resolving it every step rather than walking at where it was when this
// started: a pet follows you, so its coordinates go stale within a cycle. It is never double-clicked
// on the way - a pack beetle is rideable, so a double-click mounts you.
export const approach = (
  serial: number,
  options: {
    label: string;
    range: number;
    maxSteps: number;
    step: (spot: { x: number; y: number }) => boolean;
  },
): Mobile | undefined => {
  for (let taken = 0; taken < options.maxSteps; taken++) {
    const found = client.findObject(serial);

    if (!found || !isMobile(found)) {
      log(`${options.label}: lost track of ${hex(serial)}`);
      return undefined;
    }

    if (distanceTo(found) <= options.range) {
      return found;
    }

    if (!options.step(found)) {
      log(`${options.label}: cannot reach ${nameOf(found)}`);
      return undefined;
    }
  }

  log(`${options.label}: still not next to ${hex(serial)} after ${options.maxSteps} steps`);
  return undefined;
};
