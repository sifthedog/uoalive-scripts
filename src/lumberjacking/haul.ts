import { collectIn, packContents, type ItemPredicate } from '../lib/containers.js';
import { approach, distanceTo, hex, isMobile, nameOf } from '../lib/entity.js';
import { pickMany } from '../lib/pick.js';
import { overweight } from '../lib/weight.js';
import { isBoard } from './boards.js';
import { isLog } from './chop.js';
import {
  HAUL_BUFFER,
  MAX_PICKS,
  MAX_STEPS,
  MOVE_DELAY,
  OPL_TIMEOUT,
  PACK_ANIMAL_GRAPHICS,
  PACK_ANIMAL_SERIALS,
  SCAN_RADIUS,
  UNLOAD_RANGE,
} from './config.js';
import { isSaving } from './save.js';
import { stepToward } from './walk.js';

let reported = false;

// A list chosen rather than guessed - from config or from the cursor - is the law, so an animal out
// of sight for a moment is not a reason to go loading a stranger's mule.
let pinnedSerials: number[] = [...PACK_ANIMAL_SERIALS];

// Empty for a cursor cancelled straight away, which leaves whatever config pinned in place.
export const pickPackAnimals = (): Mobile[] => {
  // Keyed rather than appended to, because pickMany calls keyOf before its own dedupe: the same
  // animal clicked twice would otherwise be pinned twice and walked to twice per haul.
  const resolved = new Map<number, Mobile>();

  if (player.equippedItems.mount) {
    log('haul: you are mounted - dismount first if the animal you want is the one you are riding');
  }

  const picks = pickMany({
    prefix: 'haul',
    prompt: 'target the pack animals to load, ESC when done',
    maxPicks: MAX_PICKS,
    oplTimeout: OPL_TIMEOUT,

    // undefined skips the click without ending the selection, which is what a misclick on the
    // ground should cost
    keyOf: (click) => {
      const found = client.findObject(click.serial);

      if (!found || !isMobile(found)) {
        log(`haul: ${hex(click.serial)} is not a mobile`);
        return undefined;
      }

      // Not a refusal: PACK_ANIMAL_GRAPHICS is a guess at this shard, so a body it has never heard
      // of is worth reporting and then using.
      if (!PACK_ANIMAL_GRAPHICS.has(found.graphic)) {
        log(`haul: ${hex(found.graphic)} is not a body PACK_ANIMAL_GRAPHICS knows, using it anyway`);
      }

      resolved.set(found.serial, found);
      return String(found.serial);
    },
  });

  const picked = picks
    .map((pick) => resolved.get(pick.serial))
    .filter((animal): animal is Mobile => animal !== undefined);

  if (picked.length === 0) {
    log('haul: nothing picked, looking for the animals instead');
    return [];
  }

  pinnedSerials = picked.map((animal) => animal.serial);

  return picked;
};

export const findPackAnimals = (): Mobile[] => {
  if (pinnedSerials.length > 0) {
    // findObject answers with an Item for anything that is not a mobile, and a pinned serial can be
    // hand-written, so check what came back rather than trusting the number
    return pinnedSerials
      .map((serial) => client.findObject(serial))
      .filter((pinned): pinned is Mobile => pinned !== undefined && isMobile(pinned))
      .sort((a, b) => distanceTo(a) - distanceTo(b));
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
    isSaving,
  }) !== undefined;

// Moves are asynchronous, so rescan between passes rather than trusting moveItem's return value.
// A pass that shifts nothing means this animal is full, which the caller reports.
const moveAll = (packSerial: number, matches: ItemPredicate): void => {
  let previousStacks = Infinity;

  while (true) {
    const stacks = collectIn(packContents(), matches);

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
    const before = collectIn(packContents(), matches).length;
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

    const after = collectIn(packContents(), matches).length;
    if (after < before) {
      moved = true;
    }

    if (after > 0) {
      log(`haul: '${nameOf(animal)}' took ${before - after} of ${before} stacks, trying the next`);
    }
  }

  return moved;
};

// Answers whether an animal was found, not whether anything moved: one that is merely full is worth
// walking to again next cycle, and only a missing animal is worth giving up the search for.
export const unload = (): boolean => {
  const animals = findPackAnimals();

  if (animals.length === 0) {
    log('haul: no pack animal nearby');

    return false;
  }

  unloadTo(animals, isBoard);

  // A log that leaves as a log never comes back as a board, so what would not convert waits for the
  // next haul to try it again. Asked once every animal has had its turn at the boards.
  const logs = overweight(HAUL_BUFFER) ? collectIn(packContents(), isLog) : [];

  if (logs.length > 0) {
    const total = logs.reduce((sum, item) => sum + (item.amount ?? 1), 0);
    log(`haul: ${total} logs would not convert, keeping them in the pack`);
  }

  return true;
};
