import { collectIn } from '../lib/containers.js';
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

// Whether a pile has two ore in it. The amount is the only thing that answers that: the art does
// not, whatever the stack-size table says - a pile of 33 on this shard is drawn with the same
// graphic as a pile of one, so a size read off the graphic skips a full stack outright.
//
// The amount has its own trap. It is 0 for anything the client has no data for, not 1 and not
// absent, and reading a 0 as a pile of zero skips every stack in the pack - a run that halts
// overweight beside a working beetle with ore it could have smelted. So an unknown size is worth
// one attempt, and only a size the client has actually reported as one is skipped.
const bigEnough = (item: Item): boolean => {
  const amount = item.amount ?? 0;

  return amount === 0 || amount >= MIN_SMELT_AMOUNT;
};

// Why a pile was passed over, for the one log line that has to explain itself: 'smelting freed
// nothing' said over a pack with ore in it is an accusation without evidence, and every reason a
// stack is skipped is invisible from outside this file.
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

// Two conditions, and they expire differently. A written-off hue is done for the run - the shard
// has said so, or three silent passes have. A stack too small is only too small right now: one more
// swing on that vein makes it big enough, so nothing is remembered about it.
const nextOre = (writtenOff: Set<number>): Item | undefined =>
  collectIn(player.backpack?.contents, isOrePile).find(
    (item) => !writtenOff.has(item.hue ?? 0) && bigEnough(item),
  );

// Found and walked to once per smeltAll, then targeted by every pass. Held here rather than passed
// through the shared engine, which has no business knowing that this conversion needs a forge.
let forge: Mobile | undefined;

const converter = /* @__PURE__ */ createConverter({
  label: 'smelt',
  leftAs: 'leaving it as ore',
  attempts: SMELT_ATTEMPTS,
  timeoutMs: SMELT_TIMEOUT,
  pollMs: SMELT_POLL,
  delayMs: SMELT_DELAY,
  maxPasses: MAX_SMELT_PASSES,
  unskilledText: UNSKILLED_TEXT,
  isSaving,

  nextStack: (writtenOff) => nextOre(writtenOff),

  describeSkipped: (writtenOff) => {
    const piles = collectIn(player.backpack?.contents, isOrePile);

    return piles.length > 0
      ? `nothing to smelt in ${piles.length} pile(s) - ` +
          piles.map((pile) => describePile(pile, writtenOff)).join(', ')
      : undefined;
  },

  // The inverse of lumberjacking's makeBoards, which uses the tool and targets the resource: here
  // the ore is double-clicked and the beetle is the target, the same as walking up to a forge
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

export const smeltAll = (): boolean => {
  // Asked before the beetle is looked for, so a pack with nothing eligible in it costs neither a
  // search nor a walk. run() reports what it is holding and why none of it counts.
  if (!nextOre(converter.writtenOff)) {
    return converter.run();
  }

  const found = findBeetle();

  if (!found) {
    // Said once rather than every pass: a missing beetle is not fatal, the ore simply travels
    // unsmelted, and a line per cycle would bury everything else the run has to say.
    if (!reportedMissing) {
      log('smelt: no fire beetle nearby, keeping the ore as it is');
      reportedMissing = true;
    }
    return false;
  }
  reportedMissing = false;

  forge = walkToBeetle(found.serial);
  if (!forge) {
    return false;
  }

  return converter.run();
};
