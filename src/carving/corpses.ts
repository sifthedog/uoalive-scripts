import { distanceTo, hex } from '../lib/entity.js';
import { CORPSE_GRAPHIC } from './config.js';
import { memory, now } from './memory.js';

// No container filter, unlike the arrows sweep: a corpse is never inside anything. graphic reads 0
// for an entity the client is no longer tracking.
export const onGround = (): Item[] =>
  client.findAllItemsOfType(CORPSE_GRAPHIC, undefined, 'world').filter((item) => item.graphic !== 0);

// findAllItemsOfType takes a range of its own, but what it means next to a 'world' source is
// undocumented, where distanceTo is Chebyshev - which is how the shard measures reach
export const inReach = (corpses: Item[], range: number): Item[] =>
  corpses.filter((corpse) => distanceTo(corpse) <= range);

export const nearest = (corpses: Item[]): number | undefined =>
  corpses.reduce<number | undefined>(
    (best, corpse) => Math.min(distanceTo(corpse), best ?? Infinity),
    undefined,
  );

// Corpses decay, so all three sets would grow for as long as the client runs. Dropped as they are
// passed, the way the tile scan drops an expired key.
export const prune = (): void => {
  const { done, emptied, blocked } = memory();

  for (const serial of [...done, ...emptied]) {
    if (!client.findObject(serial)) {
      done.delete(serial);
      emptied.delete(serial);
    }
  }

  const time = now();

  for (const [serial, until] of blocked) {
    if (time >= until || !client.findObject(serial)) {
      blocked.delete(serial);
    }
  }
};

export const isBlocked = (serial: number): boolean => {
  const until = memory().blocked.get(serial);

  return until !== undefined && now() < until;
};

// The nearest one still worth the knife
export const nextToCarve = (corpses: Item[]): Item | undefined => {
  const { done } = memory();

  return corpses
    .filter((corpse) => !done.has(corpse.serial) && !isBlocked(corpse.serial))
    .sort((a, b) => distanceTo(a) - distanceTo(b))[0];
};

// The census, said once at startup: a wrong CORPSE_GRAPHIC is otherwise an afternoon of silence
export const describeGround = (): string => `${hex(CORPSE_GRAPHIC)} x${onGround().length}`;
