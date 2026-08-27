import { distanceTo, hex } from '../lib/entity.js';
import { AMMO_GRAPHICS } from './config.js';

// 0 and the world serial are both ways a client says 'no parent container', and which one it sends
// is not documented - reading only 0 as the ground rejected every stack on the floor
const GROUND = new Set([0, 0xffffffff]);

const parentOf = (item: Item): number => item.container >>> 0;

const onGround = (item: Item): boolean => GROUND.has(parentOf(item));

const ofType = (graphic: number): Item[] =>
  client.findAllItemsOfType(graphic, undefined, 'world');

// graphic reads 0 for an entity the client is no longer tracking
export const onFloor = (): Item[] => {
  const found = new Map<number, Item>();

  for (const graphic of AMMO_GRAPHICS) {
    for (const item of ofType(graphic)) {
      if (item.graphic !== 0 && onGround(item)) {
        found.set(item.serial, item);
      }
    }
  }

  return [...found.values()];
};

// findAllItemsOfType takes a range of its own, but what it means next to a 'world' source is
// undocumented, where distanceTo is Chebyshev - which is how the shard measures reach
export const inReach = (items: Item[], range: number): Item[] =>
  items.filter((item) => distanceTo(item) <= range);

// The parent serials are named because they are the one thing that decides whether a stack is on the
// floor, and a client that words 'no container' a third way is otherwise a silent empty sweep
export const describeFloor = (): string =>
  AMMO_GRAPHICS.map((graphic) => {
    const found = ofType(graphic);

    if (found.length === 0) {
      return `${hex(graphic)} x0`;
    }

    const parents = [...new Set(found.map((item) => hex(parentOf(item))))];

    return `${hex(graphic)} x${found.length} (under ${parents.join(', ')})`;
  }).join(', ');

// Said when the floor has stacks but none are close enough, because 'still here - watching' next to
// a pile you are standing on says nothing you can act on
export const nearest = (items: Item[]): number | undefined =>
  items.reduce<number | undefined>(
    (best, item) => Math.min(distanceTo(item), best ?? Infinity),
    undefined,
  );
