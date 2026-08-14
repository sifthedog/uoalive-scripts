import { collectIn, type ItemPredicate } from '../lib/containers.js';
import { approach, distanceTo, isMobile, nameOf } from '../lib/entity.js';
import { overweight } from '../lib/weight.js';
import { isBoard, makeBoards, retryUnconvertible, unconvertible } from './boards.js';
import { isLog } from './chop.js';
import {
  HAUL_BUFFER,
  MAX_STEPS,
  MOVE_DELAY,
  PACK_ANIMAL_GRAPHICS,
  PACK_ANIMAL_SERIALS,
  SCAN_RADIUS,
  UNLOAD_RANGE,
} from './config.js';
import { stepToward } from './walk.js';

// Boards, plus the logs of a wood this run has given up on converting. A log that is merely
// waiting its turn stays in the pack: it is worth more as boards, and the next haul retries it.
const isCargo = (item: Item): boolean => isBoard(item) || (isLog(item) && unconvertible.has(item.hue ?? 0));

let reported = false;

export const findPackAnimals = (): Mobile[] => {
  if (PACK_ANIMAL_SERIALS.length > 0) {
    // findObject answers with an Item for anything that is not a mobile, and a pinned serial is
    // only ever hand-written, so check what came back rather than trusting the number
    return PACK_ANIMAL_SERIALS.map((serial) => client.findObject(serial)).filter(
      (pinned): pinned is Mobile => pinned !== undefined && isMobile(pinned),
    );
  }

  const found: Mobile[] = [];
  for (const graphic of PACK_ANIMAL_GRAPHICS) {
    found.push(...client.findAllMobilesOfType(graphic, null, null, null, SCAN_RADIUS));
  }

  if (found.length === 0) {
    return [];
  }

  // Only your own pets can be renamed, so this is what tells yours from a stranger's
  const mine = found.filter((animal) => animal.isRenamable);
  const candidates = mine.length ? mine : found;

  if (!reported) {
    const names = candidates.map((animal) => `'${animal.name ?? '?'}'`).join(', ');
    log(`haul: ${candidates.length} pack animal(s) - ${names}`);
    reported = true;
  }

  // Nearest first, so the closest one fills before you walk past it to another
  return candidates.sort((a, b) => distanceTo(a) - distanceTo(b));
};

const animalPack = (animal: Mobile): Item | undefined => {
  const pack = client.findItemOnLayer(animal.serial, Layers.Backpack);
  if (pack) {
    return pack;
  }

  // Nothing on the layer yet, the same way a bag's contents stay undefined until it is opened.
  // The layer is asked first because this fallback is a double-click, and a giant beetle is
  // rideable - on a beetle it may mount you rather than open the pack.
  player.use(animal.serial);
  sleep(800);
  return client.findItemOnLayer(animal.serial, Layers.Backpack);
};

const walkToAnimal = (serial: number): boolean =>
  approach(serial, {
    label: 'haul',
    range: UNLOAD_RANGE,
    maxSteps: MAX_STEPS,
    step: stepToward,
  }) !== undefined;

// Moves are asynchronous, so rescan between passes rather than trusting moveItem's return value.
// A pass that shifts nothing means this animal is full, which the caller reports.
const moveAll = (packSerial: number, matches: ItemPredicate): void => {
  let previousStacks = Infinity;

  while (true) {
    const stacks = collectIn(player.backpack?.contents, matches);

    if (stacks.length === 0 || stacks.length >= previousStacks) {
      return;
    }
    previousStacks = stacks.length;

    for (const stack of stacks) {
      player.moveItem(stack.serial, packSerial);
      sleep(MOVE_DELAY);
    }
  }
};

// Works down the animals until the pack is clear or every one of them has had a turn. An animal
// that stops accepting is full rather than broken, so what is left over goes to the next one.
const unloadTo = (animals: Mobile[], matches: ItemPredicate): boolean => {
  let moved = false;

  for (const animal of animals) {
    const before = collectIn(player.backpack?.contents, matches).length;
    if (before === 0) {
      break;
    }

    if (!walkToAnimal(animal.serial)) {
      continue;
    }

    const pack = animalPack(animal);
    if (!pack) {
      log(`haul: '${nameOf(animal)}' has no reachable backpack`);
      continue;
    }

    moveAll(pack.serial, matches);

    const after = collectIn(player.backpack?.contents, matches).length;
    if (after < before) {
      moved = true;
    }

    if (after > 0) {
      log(`haul: '${nameOf(animal)}' took ${before - after} of ${before} stacks, trying the next`);
    }
  }

  return moved;
};

export const unload = (): boolean => {
  const animals = findPackAnimals();

  if (animals.length === 0) {
    log('haul: no pack animal nearby');
    return false;
  }

  const moved = unloadTo(animals, isCargo);

  // Only asked once every animal has had a turn at the boards - a full first animal is no
  // evidence the conversion fell behind. Ending the run overweight would be worse than carrying
  // logs across, but say so: boards are what belongs on an animal.
  if (overweight(HAUL_BUFFER)) {
    const logs = collectIn(player.backpack?.contents, isLog);

    if (logs.length > 0) {
      // A hue written off after three silent passes is a thin basis for carrying wood home as wood:
      // a throttled run of attempts and an axe that broke mid-conversion look exactly like a wood
      // that cannot be worked. Reopened here, where the alternative is loading logs onto an animal
      // that could have carried twice as many boards - mining reopens its own on the same reasoning,
      // and returns false once there is nothing left to reconsider, so this cannot loop.
      if (retryUnconvertible() && makeBoards()) {
        const left = collectIn(player.backpack?.contents, isLog);
        if (left.length === 0) {
          return unloadTo(animals, isCargo) || moved;
        }
      }

      const total = logs.reduce((sum, item) => sum + (item.amount ?? 1), 0);
      log(`haul: ${total} logs would not convert in time, moving them as logs`);
      return unloadTo(animals, isLog) || moved;
    }
  }

  return moved;
};
