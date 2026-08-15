import { collectIn, packContents } from '../lib/containers.js';
import { createConverter } from '../lib/convert.js';
import { approach, distanceTo, hex, isMobile, nameOf } from '../lib/entity.js';
import {
  BEETLE_SCAN_RADIUS,
  FIRE_BEETLE_GRAPHICS,
  FIRE_BEETLE_SERIAL,
  INGOT_GRAPHICS,
  MAX_BEETLE_STEPS,
  MAX_SMELT_PASSES,
  MIN_SMELT_AMOUNT,
  ORE_GRAPHICS,
  SMELT_ATTEMPTS,
  SMELT_DELAY,
  SMELT_POLL,
  SMELT_RANGE,
  SMELT_TIMEOUT,
  TARGET_TIMEOUT,
  THROTTLED_TEXT,
  UNSKILLED_TEXT,
} from './config.js';
import { isOrePile } from './ore.js';
import { isSaving } from './save.js';
import { stepToward } from './walk.js';

// Latched once found, but re-resolved through findObject every time it is used: the beetle is a
// pet and it follows you, so its coordinates go stale within a cycle.
let beetleSerial = FIRE_BEETLE_SERIAL;
let reportedFound = false;
let reportedMissing = false;

export const findBeetle = (): Mobile | undefined => {
  if (beetleSerial !== undefined) {
    const pinned = client.findObject(beetleSerial);

    if (pinned && isMobile(pinned)) {
      return pinned;
    }

    // Out of range, dead, or a hand-written serial that was never a mobile. Fall through to the
    // search rather than giving up, unless the serial came from config and is meant to be the law.
    if (FIRE_BEETLE_SERIAL !== undefined) {
      return undefined;
    }
    beetleSerial = undefined;
  }

  const found: Mobile[] = [];
  for (const graphic of FIRE_BEETLE_GRAPHICS) {
    found.push(...client.findAllMobilesOfType(graphic, null, null, null, BEETLE_SCAN_RADIUS));
  }

  if (found.length === 0) {
    return undefined;
  }

  // Only your own pets can be renamed, so this is what tells yours from a stranger's
  const mine = found.filter((beetle) => beetle.isRenamable);
  const candidates = mine.length ? mine : found;

  // Nearest first, in case two of them are standing around
  const beetle = candidates.sort((a, b) => distanceTo(a) - distanceTo(b))[0];

  if (!reportedFound) {
    log(`smelt: using '${nameOf(beetle)}' ${hex(beetle.graphic)} as the forge`);
    reportedFound = true;
  }

  beetleSerial = beetle.serial;
  return beetle;
};

const walkToBeetle = (serial: number): Mobile | undefined =>
  approach(serial, {
    label: 'smelt',
    range: SMELT_RANGE,
    maxSteps: MAX_BEETLE_STEPS,
    step: stepToward,
  });

// The stationary counterpart: a beetle not already next to you is not a forge this run can use. The
// serial is re-resolved rather than the findBeetle result trusted, because a pet's coordinates go
// stale within a cycle and distance is the one thing this asks about.
const beetleInRange = (serial: number): Mobile | undefined => {
  const found = client.findObject(serial);

  if (!found || !isMobile(found)) {
    log(`smelt: lost track of ${hex(serial)}`);
    return undefined;
  }

  const away = distanceTo(found);

  if (away > SMELT_RANGE) {
    log(`smelt: the beetle is ${away} tiles off and this run does not walk`);
    return undefined;
  }

  return found;
};

// The amount is the only thing that answers this - a pile of 33 on this shard wears the same graphic
// as a pile of one. It has its own trap: it reads 0 for anything the client has no data for, and
// reading that as a pile of zero skips every stack in the pack. So an unknown size is worth one
// attempt, and only a size the client has actually reported as one is skipped.
const bigEnough = (item: Item): boolean => {
  const amount = item.amount ?? 0;

  return amount === 0 || amount >= MIN_SMELT_AMOUNT;
};

// 'smelting freed nothing' said over a pack with ore in it is an accusation without evidence, and
// every reason a stack is skipped is invisible from outside this file.
const describePile = (item: Item, writtenOff: Set<number>): string => {
  const amount = item.amount ?? 0;
  const hue = item.hue ?? 0;

  if (writtenOff.has(hue)) {
    return `${amount} hue ${hue} (written off)`;
  }

  if (!bigEnough(item)) {
    return `${amount} hue ${hue} (too small)`;
  }

  return `${amount} hue ${hue}`;
};

// Two conditions that expire differently: a written-off hue is done for the run, while a stack too
// small is only too small right now - one more swing makes it big enough, so nothing is remembered.
const nextOre = (writtenOff: Set<number>): Item | undefined =>
  collectIn(packContents(), isOrePile).find(
    (item) => !writtenOff.has(item.hue ?? 0) && bigEnough(item),
  );

// Held here rather than passed through the shared engine, which has no business knowing that this
// conversion needs a forge.
let forge: Mobile | undefined;

// A smelt aimed at a beetle that has drifted out of range fails exactly the way an ore that cannot
// be worked does: silently. Three of those write the hue off for the run, which on a live one took
// 86 ore of a single colour out of circulation while the beetle stood two tiles further off than it
// had been. So this ends the pass instead of blaming the ore; smeltAll walks to it again next call.
const forgeGone = (): string | undefined => {
  if (!forge) {
    return 'no beetle to smelt against';
  }

  const here = client.findObject(forge.serial);

  if (!here || !isMobile(here)) {
    return `the beetle ${hex(forge.serial)} is out of sight`;
  }

  const away = distanceTo(here);

  return away > SMELT_RANGE ? `the beetle has wandered ${away} tiles off` : undefined;
};

const converter = /* @__PURE__ */ createConverter({
  label: 'smelt',
  leftAs: 'leaving it as ore',
  attempts: SMELT_ATTEMPTS,
  timeoutMs: SMELT_TIMEOUT,
  pollMs: SMELT_POLL,
  delayMs: SMELT_DELAY,
  maxPasses: MAX_SMELT_PASSES,
  unskilledText: UNSKILLED_TEXT,
  throttledText: THROTTLED_TEXT,
  isSaving,
  notNow: forgeGone,

  nextStack: (writtenOff) => nextOre(writtenOff),

  describeSkipped: (writtenOff) => {
    const piles = collectIn(packContents(), isOrePile);

    return piles.length > 0
      ? `nothing to smelt in ${piles.length} pile(s) - ` +
          piles.map((pile) => describePile(pile, writtenOff)).join(', ')
      : undefined;
  },

  // The inverse of lumberjacking's makeBoards: here the ore is double-clicked and the beetle is the
  // target, the same as walking up to a forge
  perform: (stack) => {
    if (!forge) {
      return false;
    }

    target.cancel();
    journal.clear();
    player.use(stack.serial);

    if (!target.waitTargetEntity(forge.serial, TARGET_TIMEOUT)) {
      target.cancel();
      log('smelt: no target cursor for the beetle');
      return false;
    }

    return true;
  },

  known: () => [ORE_GRAPHICS, INGOT_GRAPHICS],
  learn: (graphic) => INGOT_GRAPHICS.add(graphic),
  learned: 'ingot graphic',
});

export const unsmeltable = converter.writtenOff;
export const retryUnsmeltable = converter.retry;

// How the beetle is reached is the only thing the two smelts disagree about.
const smeltAgainst = (reach: (serial: number) => Mobile | undefined): boolean => {
  // Asked before the beetle is looked for, so a pack with nothing eligible costs neither a search
  // nor a walk
  if (!nextOre(converter.writtenOff)) {
    return converter.run();
  }

  const found = findBeetle();

  if (!found) {
    // Said once rather than every pass: a missing beetle is not fatal, the ore travels unsmelted
    if (!reportedMissing) {
      log('smelt: no fire beetle nearby, keeping the ore as it is');
      reportedMissing = true;
    }
    return false;
  }
  reportedMissing = false;

  forge = reach(found.serial);
  if (!forge) {
    return false;
  }

  return converter.run();
};

// Walks to the beetle if it has drifted, which is what dist/mining.js wants - it is about to walk
// somewhere else anyway.
export const smeltAll = (): boolean => smeltAgainst(walkToBeetle);

// Only against a beetle already in range, for the run that stands still. Costs a pass rather than
// the ore: the pack keeps it and the next call tries again.
export const smeltHere = (): boolean => smeltAgainst(beetleInRange);
