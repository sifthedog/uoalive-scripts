import { createTool } from '../lib/tool.js';
import {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  KNIFE_GRAPHICS,
  KNIFE_NAME,
  SPARE_BAG_SERIAL,
} from './config.js';

// Gated on `is` rather than handed the layer whole: Tool.serial does not check what it finds there,
// and an ungated hand would answer with the sword of a character who is mid-fight.
const inHand = (): Item | undefined => {
  const hand = player.equippedItems.oneHanded;

  return hand && knife.is(hand) ? hand : undefined;
};

const knife = /* @__PURE__ */ createTool({
  label: 'knife',
  name: KNIFE_NAME,
  graphics: KNIFE_GRAPHICS,
  spareBagSerial: SPARE_BAG_SERIAL,
  held: inHand,
  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
});

let learned: number | undefined;

// Used out of the pack and never equipped, because whoever runs this is holding a weapon they want
// to keep holding. The hand is still read first, for the character who carries the knife in it.
export const knifeSerial = (): number | undefined => {
  if (learned !== undefined && client.findObject(learned)) {
    return learned;
  }

  learned = (inHand() ?? knife.find())?.serial;

  return learned;
};

// Tests only
export const forgetKnife = (): void => {
  learned = undefined;
};
