import { describeItem } from '../lib/entity.js';
import { untilLanded } from '../lib/retry.js';
import { createTool } from '../lib/tool.js';
import {
  DISARM_ATTEMPTS,
  DISARM_POLL,
  DISARM_TIMEOUT,
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  SPARE_BAG_SERIAL,
  WEAPON_NAME,
} from './config.js';

// The two halves of this script want opposite states. CounterAttack and the rest are weapon abilities
// and are refused with an empty hand, while meditation is refused with anything in one - so the
// weapon goes to the pack for the trance and comes back for the casting, every cycle the pool runs
// down. Getting this wrong in either direction is silent and total: a run that meditates armed never
// regains mana, and one that forgets to draw casts into a permanent refusal while standing there
// defenceless.

// Drawing it again is createTool's whole job - find it, learn its graphic, get it onto a hand layer,
// reissue until it lands - and the weapon this stows is sitting in the pack where find() looks.
const weapon = /* @__PURE__ */ createTool({
  label: 'weapon',
  name: WEAPON_NAME,
  spareBagSerial: SPARE_BAG_SERIAL,

  // Either hand: a katana is one-handed and a no-dachi two-handed, and both train the same abilities
  held: () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded,

  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
});

export const held = (): Item | undefined =>
  player.equippedItems.twoHanded ?? player.equippedItems.oneHanded;

export const isWeapon = weapon.is;
export const rememberWeapon = weapon.remember;

// No-ops when the weapon is already in hand, so the loop may call it on any path it is unsure about
export const rearm = weapon.equip;

// Stowing is the half createTool has no equivalent for. The typings' own example for moveItem is this
// exact idiom - player.moveItem(player.equippedItems.robe, player.backpack) - and it is asynchronous
// like every other item move here, so it is polled for proof rather than slept on: a move the server
// threw away is indistinguishable from one still in flight.
export const disarm = (): boolean => {
  const item = held();

  if (!item) {
    return true;
  }

  // Learned now, while what is in hand is certain, so the draw afterwards matches on the graphic of
  // the weapon actually being trained with rather than on whatever WEAPON_NAME happens to find
  rememberWeapon(item);

  const pack = player.backpack?.serial;

  if (pack === undefined) {
    log(`train: nowhere to stow ${describeItem(item)} - the client reports no backpack`);

    return false;
  }

  return untilLanded({
    label: 'stow the weapon',
    attempts: DISARM_ATTEMPTS,
    timeoutMs: DISARM_TIMEOUT,
    pollMs: DISARM_POLL,
    act: () => {
      player.moveItem(item.serial, pack);
    },
    landed: () => held() === undefined,
  });
};
