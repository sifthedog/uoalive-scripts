import { movables, openNested, sift, type Wanted } from '../lib/sift.js';
import { MAX_PASSES, MOVE_DELAY, OPEN_DELAY } from './config.js';

export { artKey, wantedFrom, type Wanted } from '../lib/sift.js';

export type TransferOutcome = 'emptied' | 'stalled' | 'unopened';

export interface Transferred {
  outcome: TransferOutcome;
  stacks: number;
  items: number;
  left: number;
}

export const transfer = (
  sourceSerial: number,
  destSerial: number,
  wanted: Wanted,
  onMove?: (item: Item) => void,
): Transferred => {
  player.use(sourceSerial);
  sleep(OPEN_DELAY);

  // Amounts are read at the moment of the move, because a stack that has already gone answers for
  // wherever it is now. Keyed by serial, so an item a failed pass left behind is not counted twice.
  const sent = new Map<number, number>();
  const opened = new Set<number>();
  const look = () => sift(sourceSerial, { skipSerial: destSerial, opened });

  const result = (outcome: TransferOutcome, left: number): Transferred => ({
    outcome,
    stacks: sent.size,
    items: [...sent.values()].reduce((total, amount) => total + amount, 0),
    left,
  });

  let previous = Infinity;

  for (let pass = 0; pass < MAX_PASSES; pass++) {
    const found = look();

    if (!found.readable) {
      return result('unopened', 0);
    }

    if (openNested(found.containers, opened, OPEN_DELAY)) {
      // What has just become readable has never been counted, so the stall check starts over
      previous = Infinity;
      continue;
    }

    const todo = movables(found, wanted);

    if (todo.length === 0) {
      return result('emptied', 0);
    }

    // Moves are asynchronous - moveItem's return says only that the packet went out - so a pass is
    // judged by rescanning, and one that shifted nothing is a stall rather than an empty container
    if (todo.length >= previous) {
      return result('stalled', todo.length);
    }
    previous = todo.length;

    for (const item of todo) {
      player.moveItem(item.serial, destSerial);
      sent.set(item.serial, item.amount ?? 1);
      onMove?.(item);
      sleep(MOVE_DELAY);
    }
  }

  return result('stalled', movables(look(), wanted).length);
};
