import { collectIn, contentsOf, forgetUnreadable } from '../lib/containers.js';
import { hex, isMobile } from '../lib/entity.js';
import {
  BLOCKED_DELAY,
  MOVE_DELAY,
  OPEN_DELAY,
  SETTLE_POLL,
  SETTLE_TIMEOUT,
  TAKE_GRAPHICS,
} from './config.js';
import { isBlocked } from './corpses.js';
import { memory, now } from './memory.js';

export interface Taken {
  stacks: number;
  items: number;
}

const wanted = (item: Item): boolean => TAKE_GRAPHICS.has(item.graphic);

const corpseAt = (serial: number): Item | undefined => {
  const found = client.findObject(serial);

  return found && !isMobile(found) ? found : undefined;
};

const held = (serial: number): Item[] | undefined => contentsOf(corpseAt(serial));

const landed = (serial: number, moved: Item[]): Taken => {
  const left = new Set((held(serial) ?? []).map((item) => item.serial));
  const gone = moved.filter((item) => !left.has(item.serial));

  return {
    stacks: gone.length,
    items: gone.reduce((total, item) => total + (item.amount ?? 1), 0),
  };
};

// Polled rather than slept through: moveItem's return says only that the packet went out, and a move
// that lands in 100ms would otherwise cost the worst case every time.
const settle = (serial: number, moved: Item[]): Taken => {
  let took = landed(serial, moved);

  for (let waited = 0; waited < SETTLE_TIMEOUT && took.stacks < moved.length; waited += SETTLE_POLL) {
    sleep(SETTLE_POLL);
    took = landed(serial, moved);
  }

  return took;
};

// Carved, and not yet found to be empty. Never a corpse that has not been carved: contents stay
// undefined until it is opened, so asking costs a cycle whatever the answer.
export const pending = (corpses: Item[]): Item | undefined => {
  const { done, emptied } = memory();

  return corpses.find(
    (corpse) =>
      done.has(corpse.serial) && !emptied.has(corpse.serial) && !isBlocked(corpse.serial),
  );
};

export const take = (corpse: Item, packSerial: number): Taken => {
  player.use(corpse.serial);
  sleep(OPEN_DELAY);

  // Opening a container is what makes it readable, so the throw latched on the way in is cleared
  forgetUnreadable(corpse.serial);

  const { emptied } = memory();
  const contents = held(corpse.serial);

  if (contents === undefined) {
    emptied.add(corpse.serial);
    log(`carve: ${hex(corpse.serial)} would not say what it holds, leaving it`);

    return { stacks: 0, items: 0 };
  }

  const stacks = collectIn(contents, wanted);

  if (stacks.length === 0) {
    emptied.add(corpse.serial);

    return { stacks: 0, items: 0 };
  }

  stacks.forEach((item, index) => {
    // The gap goes between the moves rather than after each, so a haul of one pays no delay at all
    if (index > 0) {
      sleep(MOVE_DELAY);
    }

    player.moveItem(item.serial, packSerial);
  });

  const took = settle(corpse.serial, stacks);

  if (took.stacks === stacks.length) {
    emptied.add(corpse.serial);
  } else {
    // Still pending, so without this the next cycle reopens the same corpse - which walked a run to
    // the stall watchdog's stop a 'looting' cycle at a time
    memory().blocked.set(corpse.serial, now() + BLOCKED_DELAY);
    log(
      `carve: ${hex(corpse.serial)} kept ${stacks.length - took.stacks} of them, ` +
        `leaving it for ${BLOCKED_DELAY / 1000}s`,
    );
  }

  return took;
};
