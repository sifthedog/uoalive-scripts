import { MOVE_DELAY, SETTLE_POLL, SETTLE_TIMEOUT } from './config.js';

export interface Moved {
  serial: number;
  amount: number;
}

export interface Took {
  stacks: number;
  items: number;
}

// The amount is snapshotted here rather than read back off the handle: a stack that merged into an
// identical one at the destination answers for wherever it is now
export const issue = (items: Item[], destSerial: number): Moved[] =>
  items.map((item, index) => {
    // The gap goes between the moves rather than after each, since the throttle is about the
    // interval between actions
    if (index > 0) {
      sleep(MOVE_DELAY);
    }

    player.moveItem(item.serial, destSerial);

    return { serial: item.serial, amount: item.amount ?? 1 };
  });

// moveItem's return says only that the packet went out, so what went is judged by rescanning. An
// item still in the pack is never counted, which is what keeps a refused pass off the tally.
export const landed = (sent: Moved[], after: Item[]): Took => {
  const left = new Set(after.map((item) => item.serial));
  const gone = sent.filter((moved) => !left.has(moved.serial));

  return {
    stacks: gone.length,
    items: gone.reduce((total, moved) => total + moved.amount, 0),
  };
};

// Polled rather than slept through: a move that lands in 100ms otherwise costs the worst case, and
// this loop pays it all afternoon
export const settle = (sent: Moved[], rescan: () => Item[]): Took => {
  let took = landed(sent, rescan());

  let waited = 0;

  for (; waited < SETTLE_TIMEOUT && took.stacks < sent.length; waited += SETTLE_POLL) {
    sleep(SETTLE_POLL);
    took = landed(sent, rescan());
  }

  return took;
};
