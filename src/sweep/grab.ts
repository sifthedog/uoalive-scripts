import { COIN_GRAPHICS, MOVE_DELAY, SETTLE_POLL, SETTLE_TIMEOUT } from './config.js';

export interface Swept {
  stacks: number;
  items: number;
  coins: number;
}

const COINS = new Set(COIN_GRAPHICS);

export const sweep = (packSerial: number, reachable: Item[]): void => {
  reachable.forEach((item, index) => {
    // The gap goes between the moves rather than after each: the throttle is about the interval
    // between actions, so a sweep of one used to pay a delay it had nothing to space out from
    if (index > 0) {
      sleep(MOVE_DELAY);
    }

    player.moveItem(item.serial, packSerial);
  });
};

// moveItem's return says only that the packet went out, so what went is judged by rescanning. A
// stack still on the floor is never counted, which is what keeps a refused sweep off the tally.
export const landed = (swept: Item[], after: Item[]): Swept => {
  const left = new Set(after.map((item) => item.serial));
  const gone = swept.filter((item) => !left.has(item.serial));

  const amountOf = (items: Item[]): number =>
    items.reduce((total, item) => total + (item.amount ?? 1), 0);

  return {
    stacks: gone.length,
    items: amountOf(gone.filter((item) => !COINS.has(item.graphic))),
    coins: amountOf(gone.filter((item) => COINS.has(item.graphic))),
  };
};

// Coins are counted apart from the rest because summing 12 arrows and 312 gold into 324 is a number
// that means nothing
export const describeTake = (took: Pick<Swept, 'items' | 'coins'>): string => {
  const halves = [];

  if (took.items > 0) {
    halves.push(`${took.items} ${took.items === 1 ? 'arrow' : 'arrows'}`);
  }

  if (took.coins > 0) {
    halves.push(`${took.coins} gold`);
  }

  return halves.join(' and ') || 'nothing';
};

// Polled rather than slept through, which is drop.ts's lesson in reverse: a move that lands in 100ms
// otherwise costs the worst case every time, and the worst case is what a sweep used to always pay.
export const settle = (swept: Item[], rescan: () => Item[]): Swept => {
  let took = landed(swept, rescan());

  for (let waited = 0; waited < SETTLE_TIMEOUT && took.stacks < swept.length; waited += SETTLE_POLL) {
    sleep(SETTLE_POLL);
    took = landed(swept, rescan());
  }

  return took;
};
