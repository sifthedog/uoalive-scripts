import { findIn, openContainers } from '../lib/containers.js';
import {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  PICKAXE_NAME,
  SPARE_BAG_SERIAL,
} from './config.js';

let pickaxeGraphic: number | undefined;
let spareBagSerial = SPARE_BAG_SERIAL;
let reportedEmpty = false;

// Names are empty until the client has tooltip data, so prefer the graphic once we know it
export const isPickaxe = (item: Item): boolean =>
  (pickaxeGraphic !== undefined && item.graphic === pickaxeGraphic) ||
  (item.name ?? '').toLowerCase().includes(PICKAXE_NAME);

export const rememberPickaxe = (item: Item | undefined): void => {
  if (item && pickaxeGraphic === undefined) {
    pickaxeGraphic = item.graphic;
    log(`pickaxe graphic is 0x${item.graphic.toString(16)}`);
  }
};

// Every graphic the search actually saw, one level down included. Listing only the top level read
// as an empty pack when the spares were in a bag, which is exactly the case this message exists
// for - openContainers opens the top level of the pack and no deeper, so a bag inside a bag is
// never reached and SPARE_BAG_SERIAL is the way out.
const describeContents = (contents: Item[] | undefined): string =>
  (contents ?? [])
    .map((item) => {
      const graphic = `0x${item.graphic.toString(16)}`;
      return item.contents?.length ? `${graphic}[${describeContents(item.contents)}]` : graphic;
    })
    .join(', ');

const reportEmptyPack = (): void => {
  if (reportedEmpty) {
    return;
  }

  log(`equipPickaxe: no pickaxe found. Pack holds: ${describeContents(player.backpack?.contents)}`);
  log('equipPickaxe: if the spares are in a bag inside a bag, pin it as SPARE_BAG_SERIAL');
  reportedEmpty = true;
};

// A broken pickaxe can linger in equippedItems, and isPickaxe would happily match it by
// graphic. A destroyed serial stops resolving, so ask the world rather than the layer.
const stillHolding = (): boolean => {
  const held = player.equippedItems.oneHanded;

  if (!held || !isPickaxe(held)) {
    return false;
  }

  return client.findObject(held.serial) !== undefined;
};

// What dig.ts watches to spot a tool that wore out mid-swing: a RunUO tool tracks UsesRemaining
// rather than hits, and item.hits is 0 for anything the client knows nothing about, so a serial
// that stops resolving is the only reliable evidence.
export const pickaxeSerial = (): number | undefined => player.equippedItems.oneHanded?.serial;

export const equipPickaxe = (): boolean => {
  if (stillHolding()) {
    return true;
  }

  let pickaxe = findIn(player.backpack?.contents, isPickaxe);

  if (!pickaxe && openContainers(spareBagSerial)) {
    pickaxe = findIn(player.backpack?.contents, isPickaxe);
  }

  if (!pickaxe) {
    client.headMsg('No pickaxe!', player, 33);
    reportEmptyPack();
    return false;
  }

  reportedEmpty = false;
  rememberPickaxe(pickaxe);

  // Remember the bag it came from so the next break reopens only that one
  if (pickaxe.container && pickaxe.container !== player.backpack?.serial) {
    spareBagSerial = pickaxe.container;
  }

  // A cursor left open by the swing that broke the pickaxe would swallow the equip
  target.cancel();

  for (let attempt = 1; attempt <= EQUIP_ATTEMPTS; attempt++) {
    player.equip(pickaxe.serial);

    // equip is asynchronous - do not swing until it has landed on the hand layer
    for (let waited = 0; waited < EQUIP_TIMEOUT; waited += EQUIP_POLL) {
      sleep(EQUIP_POLL);
      if (player.equippedItems.oneHanded?.serial === pickaxe.serial) {
        return true;
      }
    }

    log(`equipPickaxe: attempt ${attempt} did not land, reissuing`);
  }

  log('equipPickaxe: gave up equipping');
  return false;
};
