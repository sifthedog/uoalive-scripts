import { collectIn } from '../lib/containers.js';
import { countsByGraphic, diffCounts, type Change, type Counts } from '../lib/pack.js';
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

// Hues this run has given up on, so a stack that cannot be smelted stops being picked every pass
export const unsmeltable = new Set<number>();

const distanceTo = (entity: { x: number; y: number }) =>
  Math.max(Math.abs(entity.x - player.x), Math.abs(entity.y - player.y));

// _tag is how the client's own typings tell an Item from a Mobile, and it costs no round trip
const isMobile = (entity: Item | Mobile): entity is Mobile => entity._tag === 'Mobile';

// Latched once found, but re-resolved through findObject every time it is used: the beetle is a
// pet and it follows you, so its coordinates go stale within a cycle.
let beetleSerial = FIRE_BEETLE_SERIAL;
let reportedFound = false;
let reportedMissing = false;

const nameOf = (beetle: Mobile): string => beetle.name ?? `0x${beetle.serial.toString(16)}`;

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
    log(`smelt: using '${nameOf(beetle)}' 0x${beetle.graphic.toString(16)} as the forge`);
    reportedFound = true;
  }

  beetleSerial = beetle.serial;
  return beetle;
};

// The beetle moves, so re-resolve it every step rather than walking at where it was when the smelt
// started. It is never double-clicked on the way: a fire beetle is rideable, so a double-click
// mounts you - the exact thing mount.ts exists to undo.
const approach = (serial: number): Mobile | undefined => {
  for (let step = 0; step <= MAX_BEETLE_STEPS; step++) {
    const beetle = client.findObject(serial);

    if (!beetle || !isMobile(beetle)) {
      log('smelt: lost track of the fire beetle');
      return undefined;
    }

    if (distanceTo(beetle) <= SMELT_RANGE) {
      return beetle;
    }

    if (!stepToward(beetle)) {
      log('smelt: cannot reach the fire beetle');
      return undefined;
    }
  }

  log(`smelt: still not next to the fire beetle after ${MAX_BEETLE_STEPS} steps`);
  return undefined;
};

// The smelt sends no message on stock RunUO, only a sound, so the pack diff is the only evidence of
// it. That diff also names this shard's ingot graphics, whatever the art ids turn out to be.
const learnIngots = (changes: Change[]): void => {
  for (const { key, delta } of changes) {
    if (delta <= 0) {
      continue;
    }

    const graphic = Number(key.split('/')[0]);
    if (ORE_GRAPHICS.has(graphic) || INGOT_GRAPHICS.has(graphic)) {
      continue;
    }

    INGOT_GRAPHICS.add(graphic);
    log(`smelt: ingot graphic is 0x${graphic.toString(16)}`);
  }
};

// Watch the pack rather than sleeping a fixed amount and reading once. The action throttle can hold
// a smelt well past any pause worth taking, and reading too early is indistinguishable from an ore
// that cannot be worked - which is how a hue gets written off while it was only running late.
const waitForChange = (before: Counts): Change[] => {
  for (let waited = 0; waited < SMELT_TIMEOUT; waited += SMELT_POLL) {
    sleep(SMELT_POLL);

    const changes = diffCounts(before, countsByGraphic());
    if (changes.length > 0) {
      return changes;
    }
  }

  return [];
};

// Silent misses per hue, cleared by a success, so only a hue that fails repeatedly is given up on
const misses = new Map<number, number>();

// Counts one failure against a hue and gives up on it once they add up. Every failing path has to
// come through here: one that returned without counting would leave the candidate set unchanged,
// so the next pass picks the same stack and the loop runs to its backstop instead of shrinking.
const missed = (stackHue: number): void => {
  const count = (misses.get(stackHue) ?? 0) + 1;
  misses.set(stackHue, count);

  if (count >= SMELT_ATTEMPTS) {
    unsmeltable.add(stackHue);
    log(`smelt: hue ${stackHue} failed ${count} times, leaving it as ore`);
  }
};

// The inverse of lumberjacking's makeBoards, which uses the tool and targets the resource: here the
// ore is the thing double-clicked and the beetle is the target, the same as walking up to a forge.
const smeltStack = (stack: Item, beetle: Mobile): boolean => {
  const stackHue = stack.hue ?? 0;
  const before = countsByGraphic();

  // A cursor left open by the last swing would swallow this one
  target.cancel();
  journal.clear();
  player.use(stack.serial);

  if (!target.waitTargetEntity(beetle.serial, TARGET_TIMEOUT)) {
    target.cancel();
    log('smelt: no target cursor for the beetle');
    missed(stackHue);
    return false;
  }

  const changes = waitForChange(before);
  if (changes.length > 0) {
    misses.delete(stackHue);
    learnIngots(changes);
    return true;
  }

  // The shard saying it outright is worth acting on immediately; a coloured ore needs the Mining
  // skill to work it, and no amount of retrying supplies that.
  if (UNSKILLED_TEXT.some((text) => journal.containsText(text))) {
    unsmeltable.add(stackHue);
    log(`smelt: not skilled enough for hue ${stackHue}, leaving it as ore`);
    return false;
  }

  // Otherwise it was silent, which is also what a throttled or stale attempt looks like
  missed(stackHue);

  return false;
};

// Written off is not the same as impossible. Three silent passes is a thin basis for carrying a
// hue home - a beetle that wandered out of range, a run of throttled attempts and a stack that was
// briefly too small all look exactly like an ore that cannot be worked. So when the alternative is
// ending the run overweight on a pack full of ore, the loop clears the write-offs and tries again
// rather than taking the earlier verdict as final.
export const retryUnsmeltable = (): boolean => {
  if (unsmeltable.size === 0) {
    return false;
  }

  log(`smelt: giving ${unsmeltable.size} hue(s) written off earlier another go`);
  unsmeltable.clear();
  misses.clear();

  return true;
};

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

// Two conditions, and they expire differently. A hue in `unsmeltable` is done for the run - the
// shard has said so, or three silent passes have. A stack too small is only too small right now:
// one more swing on that vein makes it big enough, so nothing is remembered about it.
const nextStack = (): Item | undefined =>
  collectIn(player.backpack?.contents, isOrePile).find(
    (item) => !unsmeltable.has(item.hue ?? 0) && bigEnough(item),
  );

// Why a pile was passed over, for the one log line that has to explain itself: 'smelting freed
// nothing' said over a pack with ore in it is an accusation without evidence, and every reason a
// stack is skipped is invisible from outside this file.
const describePile = (item: Item): string => {
  const amount = item.amount ?? 0;
  const hue = item.hue ?? 0;

  if (unsmeltable.has(hue)) {
    return `${amount} hue ${hue} (written off)`;
  }

  if (!bigEnough(item)) {
    return `${amount} hue ${hue} (too small)`;
  }

  return `${amount} hue ${hue}`;
};

export const smeltAll = (): boolean => {
  if (!nextStack()) {
    // Nothing eligible is the ordinary case with an empty pack and a mystery with a full one, so
    // the full one says what it is holding and why none of it counts
    const piles = collectIn(player.backpack?.contents, isOrePile);
    if (piles.length > 0) {
      log(`smelt: nothing to smelt in ${piles.length} pile(s) - ${piles.map(describePile).join(', ')}`);
    }

    return true;
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

  const beetle = approach(found.serial);
  if (!beetle) {
    return false;
  }

  // One stack per pass, then rescan: a smelt consumes the stack and creates a new item, so every
  // other serial in a snapshot goes stale the moment the first one converts.
  for (let pass = 0; pass < MAX_SMELT_PASSES; pass++) {
    // A frozen shard answers a smelt the same way an unworkable ore does - with nothing at all - so
    // without this the world save costs three attempts and the hue is written off for the rest of
    // the run. Left for the caller: the pack is still heavy, so the next cycle comes straight back.
    if (isSaving()) {
      log('smelt: the world is saving, leaving the ore for now');
      return false;
    }

    const stack = nextStack();

    if (!stack) {
      return true;
    }

    smeltStack(stack, beetle);
    sleep(SMELT_DELAY);
  }

  // Termination does not rest on this: a hue either smelts or is given up on after SMELT_ATTEMPTS,
  // so the candidate set always shrinks. This is the backstop.
  log(`smelt: hit the ${MAX_SMELT_PASSES} pass backstop`);
  return false;
};
