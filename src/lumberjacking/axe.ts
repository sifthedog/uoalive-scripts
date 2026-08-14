import { findIn, openContainers } from '../lib/containers.js';
import {
  AXE_NAME,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  SPARE_BAG_SERIAL,
} from './config.js';

let axeGraphic: number | undefined;
let spareBagSerial = SPARE_BAG_SERIAL;
let reportedEmpty = false;

// Axes are two-handed, hatchets are one-handed, and either will chop
const held = (): Item | undefined =>
  player.equippedItems.twoHanded ?? player.equippedItems.oneHanded;

// Names are empty until the client has tooltip data, so prefer the graphic once we know it
export const isAxe = (item: Item): boolean =>
  (axeGraphic !== undefined && item.graphic === axeGraphic) ||
  (item.name ?? '').toLowerCase().includes(AXE_NAME);

export const rememberAxe = (item: Item | undefined): void => {
  if (item && axeGraphic === undefined) {
    axeGraphic = item.graphic;
    log(`axe graphic is 0x${item.graphic.toString(16)}`);
  }
};

const reportEmptyPack = (): void => {
  if (reportedEmpty) {
    return;
  }

  const graphics = (player.backpack?.contents ?? [])
    .map((item) => `0x${item.graphic.toString(16)}`)
    .join(', ');
  log(`equipAxe: no axe found. Top level of pack holds: ${graphics}`);
  reportedEmpty = true;
};

// A broken axe can linger in equippedItems, and isAxe would happily match it by graphic.
// A destroyed serial stops resolving, so ask the world rather than the layer.
const stillHolding = (): boolean => {
  const item = held();

  if (!item || !isAxe(item)) {
    return false;
  }

  return client.findObject(item.serial) !== undefined;
};

// The serial the chop is swung with, so a worn-out axe can be spotted by it no longer resolving
export const axeSerial = (): number | undefined => held()?.serial;

export const equipAxe = (): boolean => {
  if (stillHolding()) {
    return true;
  }

  let axe = findIn(player.backpack?.contents, isAxe);

  if (!axe && openContainers(spareBagSerial)) {
    axe = findIn(player.backpack?.contents, isAxe);
  }

  if (!axe) {
    client.headMsg('No axe!', player, 33);
    reportEmptyPack();
    return false;
  }

  reportedEmpty = false;
  rememberAxe(axe);

  // Remember the bag it came from so the next break reopens only that one
  if (axe.container && axe.container !== player.backpack?.serial) {
    spareBagSerial = axe.container;
  }

  // A cursor left open by the chop that broke the axe would swallow the equip
  target.cancel();

  for (let attempt = 1; attempt <= EQUIP_ATTEMPTS; attempt++) {
    player.equip(axe.serial);

    // equip is asynchronous - do not chop until it has landed on a hand layer
    for (let waited = 0; waited < EQUIP_TIMEOUT; waited += EQUIP_POLL) {
      sleep(EQUIP_POLL);
      if (held()?.serial === axe.serial) {
        return true;
      }
    }

    log(`equipAxe: attempt ${attempt} did not land, reissuing`);
  }

  log('equipAxe: gave up equipping');
  return false;
};
