// Taking the weapon out of the character's hands and putting it back: a weapon ability is refused
// with an empty hand, while meditation is refused with anything in one. Getting it wrong is silent
// and total in both directions - a run that meditates armed never regains mana, and one that forgets
// to draw casts into a permanent refusal while standing there defenceless.
//
// A factory, because createTool underneath it latches the graphic it learned.

import { describeItem } from './entity.js';
import { untilLanded } from './retry.js';
import { createTool } from './tool.js';

export interface WeaponOptions {
  prefix: string;

  // A substring, matched case-insensitively. Only used for a draw that cannot use the graphic - the
  // graphic is learned from whatever is actually in hand and matched on from then on.
  name: string;

  // openContainers opens the top level of the pack and no deeper.
  spareBagSerial?: number;

  equip: { attempts: number; timeoutMs: number; pollMs: number };

  // Its own trio rather than the equip one, though they hold the same numbers today: an equip and a
  // stow are independent facts about the shard.
  disarm: { attempts: number; timeoutMs: number; pollMs: number };
}

export interface Weapon {
  // Either hand: a katana is one-handed and a no-dachi two-handed, and both train the same abilities
  held: () => Item | undefined;

  is: (item: Item) => boolean;
  remember: (item: Item | undefined) => void;

  // No-ops when the weapon is already in hand, so a loop may call it on any path it is unsure about
  rearm: () => boolean;

  disarm: () => boolean;
}

export const createWeapon = ({
  prefix,
  name,
  spareBagSerial,
  equip,
  disarm,
}: WeaponOptions): Weapon => {
  const held = (): Item | undefined =>
    player.equippedItems.twoHanded ?? player.equippedItems.oneHanded;

  // Drawing it again is createTool's whole job, and the weapon this stows is sitting in the pack
  // where its find() looks.
  const tool = createTool({ label: 'weapon', name, spareBagSerial, held, equip });

  return {
    held,
    is: tool.is,
    remember: tool.remember,
    rearm: tool.equip,

    // Polled for proof rather than slept on: a move the server threw away is indistinguishable from
    // one still in flight.
    disarm: () => {
      const item = held();

      if (!item) {
        return true;
      }

      // Learned while what is in hand is certain, so the draw afterwards matches on the weapon
      // actually being trained with rather than on whatever `name` happens to find
      tool.remember(item);

      const pack = player.backpack?.serial;

      if (pack === undefined) {
        log(`${prefix}: nowhere to stow ${describeItem(item)} - the client reports no backpack`);

        return false;
      }

      return untilLanded({
        label: 'stow the weapon',
        attempts: disarm.attempts,
        timeoutMs: disarm.timeoutMs,
        pollMs: disarm.pollMs,
        act: () => {
          player.moveItem(item.serial, pack);
        },
        landed: () => held() === undefined,
      });
    },
  };
};
