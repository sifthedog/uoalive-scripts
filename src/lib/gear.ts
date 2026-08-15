// Taking the character's kit off for a trance and putting the same pieces back afterwards. By serial
// rather than by name or graphic: the gear worth wearing carries Faster Casting and Mana
// Regeneration, so *that* ring has to go back on, not whichever lookalike a search finds first.
//
// Two passes rather than one. The hands come off for every trance; the armour only once the shard has
// refused a trance with the hands already empty, and then the lesson latches. Stripping armour that
// did not need to come off would pay for the trance with the mana regeneration that shortens it.
//
// A factory, because both the remembered pieces and that latched lesson are per-run state.

import { describeItem, hex } from './entity.js';
import { untilLanded } from './retry.js';

// `Layers` is declared globally as a value only, so the enum's *type* has to be reached through the
// module it is declared in. Exported so a folder's config can annotate its own strip list.
export type Layer = import('enums').Layers;

// The rollback record, written while the character is still wearing the piece: a burst that
// half-lands must still be restorable. graphic and name are carried only so the log can name a piece
// the client has since stopped resolving.
interface Piece {
  serial: number;
  layer: Layer;
  graphic: number;
  name?: string;
}

export interface GearOptions {
  prefix: string;

  // In strip order, which is also restore order. Hand layers first: they are the only ones whose
  // absence ends a run, so they get the first attempt and the freshest budget on the way back.
  layers: Layer[];

  // Pause between the individual moves inside one burst, to stay under the action throttle
  moveDelayMs: number;

  equip: { attempts: number; timeoutMs: number; pollMs: number };

  // Its own trio rather than the equip one: an equip and a stow are independent facts about the shard
  disarm: { attempts: number; timeoutMs: number; pollMs: number };

  // The by-graphic draw from weapon.ts, for the one thing an exact-serial restore cannot answer: the
  // weapon stopped resolving while it sat in the pack. An armed character beats a right one.
  rearm?: () => boolean;

  // Skip the escalation on a shard already known to block on armour, at the cost of stripping on
  // every trance whether it was needed or not
  stripAtOnce?: boolean;
}

export interface Gear {
  // Clears the hands - or everything, once the shard has taught this module better. Answers whether
  // the hands came clear, which is the part meditation universally requires.
  stow: () => boolean;

  // Asked for only when a trance was refused with the hands already empty. Answering false is what
  // tells the caller the escalation is spent.
  stripMore: () => boolean;

  restore: () => boolean;

  // One line for the preflight, naming what sits on the strip layers right now
  survey: () => string;
}

export const createGear = (options: GearOptions): Gear => {
  const { prefix } = options;

  // Split inside the factory rather than at module scope: Layers is an ambient global, and a
  // module-level read happens at import time, before a test has installed one.
  const isHand = (layer: Layer): boolean =>
    layer === Layers.OneHanded || layer === Layers.TwoHanded;

  const hands = options.layers.filter(isHand);
  const rest = options.layers.filter((layer) => !isHand(layer));

  // In the order they came off, which is the order they go back on
  let stowed: Piece[] = [];

  // The latched lesson: this shard refuses a trance with armour on
  let deep = options.stripAtOnce ?? false;

  // Said once per piece rather than once per trance: a glove that will not go back on is worth a line
  // the first time and noise for the next two hours.
  const reported = new Set<number>();

  // findItemOnLayer rather than player.equippedItems, which is keyed by name: a Layers[] out of a
  // config could only reach that object through a hand-written map that would rot silently.
  const wornOn = (layer: Layer): Item | undefined => client.findItemOnLayer(player.serial, layer);

  const off = (piece: Piece): boolean => wornOn(piece.layer)?.serial !== piece.serial;

  const on = (piece: Piece): boolean => wornOn(piece.layer)?.serial === piece.serial;

  // Never part of a `landed` test: a shard whose findObject does not answer for pack contents would
  // make every piece look destroyed, and a wait that read that as success would equip nothing. Only
  // used afterwards, to decide whether retrying next trance is worth anything.
  const gone = (piece: Piece): boolean => client.findObject(piece.serial) === undefined;

  const remember = (piece: Piece): void => {
    if (!stowed.some((held) => held.serial === piece.serial)) {
      stowed.push(piece);
    }
  };

  // One untilLanded over the whole set rather than one per layer: fifteen sequential calls cost
  // fifteen independent timeoutMs windows in the bad case, where a burst costs one for all of them.
  const clearLayers = (targets: Layer[], label: string): number => {
    const worn = targets
      .map((layer) => ({ layer, item: wornOn(layer) }))
      .filter((found): found is { layer: Layer; item: Item } => found.item !== undefined);

    if (worn.length === 0) {
      return 0;
    }

    const pack = player.backpack?.serial;

    if (pack === undefined) {
      log(`${prefix}: nowhere to stow ${worn.length} piece(s) - the client reports no backpack`);

      return 0;
    }

    const pieces: Piece[] = worn.map(({ layer, item }) => ({
      serial: item.serial,
      layer,
      graphic: item.graphic,
      name: item.name,
    }));

    // Before the first move and not after the last: a burst that moves four and fails on the fifth
    // has to leave a record of all five, or those four stay in the pack for the rest of the run
    pieces.forEach(remember);

    untilLanded({
      label,
      attempts: options.disarm.attempts,
      timeoutMs: options.disarm.timeoutMs,
      pollMs: options.disarm.pollMs,

      // Idempotent, because untilLanded reissues act() wholesale: without the skip a reissue would
      // bounce every piece that already landed back out of the pack and in again.
      act: () => {
        for (const piece of pieces) {
          if (off(piece)) {
            continue;
          }

          player.moveItem(piece.serial, pack);
          sleep(options.moveDelayMs);
        }
      },

      // Serial and not emptiness: if something else has landed on that layer, ours still came off
      landed: () => pieces.every(off),
    });

    return pieces.filter(off).length;
  };

  // Answers true for a strip list with no hand layers at all, which is a run that has decided its
  // hands are not the problem.
  const handsClear = (): boolean => !hands.some((layer) => wornOn(layer) !== undefined);

  return {
    survey: () => {
      const worn = options.layers
        .map((layer) => wornOn(layer))
        .filter((item): item is Item => item !== undefined);

      if (worn.length === 0) {
        return 'nothing on the strip layers - if the paperdoll disagrees, check STRIP_LAYERS';
      }

      return `${worn.length} piece(s) come off for a trance: ${worn.map(describeItem).join(', ')}`;
    },

    stow: () => {
      const targets = deep ? [...hands, ...rest] : hands;
      const label = deep ? 'strip for the trance' : 'stow what is in hand';

      clearLayers(targets, label);

      // The hands and not the whole strip: one piece of armour that will not move - cursed, or a
      // pack at the 120 cap - would otherwise stop this run meditating ever again, where the trance
      // very likely still works. If it does not, the shard says so.
      const clear = handsClear();

      if (!clear) {
        log(`${prefix}: could not clear both hands, so the trance will be refused`);
      }

      return clear;
    },

    stripMore: () => {
      // Already spent. Answering false is what stops the caller escalating for ever, with no counter.
      if (deep) {
        return false;
      }

      const moved = clearLayers(rest, 'strip the armour');

      // Latched even when the strip only partly landed: the fact recorded is about the shard's rules,
      // not about whether this burst of moves got through.
      deep = true;

      return moved > 0;
    },

    restore: () => {
      // Load-bearing rather than tidy: the caller calls this on every way out of a wait, including
      // the ones where the stow found nothing to take.
      if (stowed.length === 0) {
        return true;
      }

      const wanted = [...stowed];

      // A cursor left open by whatever came before would swallow the first equip
      target.cancel();

      untilLanded({
        label: 'put the gear back on',
        attempts: options.equip.attempts,
        timeoutMs: options.equip.timeoutMs,
        pollMs: options.equip.pollMs,

        act: () => {
          for (const piece of wanted) {
            if (on(piece)) {
              continue;
            }

            player.equip(piece.serial);
            sleep(options.moveDelayMs);
          }
        },

        landed: () => wanted.every(on),
      });

      // What is still not back divides in two, and the difference is only whether trying again next
      // trance could ever work
      const missing = wanted.filter((piece) => !on(piece));
      const destroyed = new Set(missing.filter(gone).map((piece) => piece.serial));

      // A piece that came back has earned its line again if it ever fails later, which over a
      // two-hour run is the difference between a quiet log and a lying one
      for (const piece of wanted) {
        if (on(piece)) {
          reported.delete(piece.serial);
        }
      }

      for (const piece of missing) {
        if (destroyed.has(piece.serial)) {
          log(`${prefix}: ${describeItem(piece)} ${hex(piece.serial)} is gone - not putting it back`);
        }
      }

      stowed = missing.filter((piece) => !destroyed.has(piece.serial));

      for (const piece of stowed) {
        if (!reported.has(piece.serial)) {
          reported.add(piece.serial);
          log(`${prefix}: ${describeItem(piece)} would not go back on - will try again next trance`);
        }
      }

      // Something is in hand, which is all the casting half needs. Whether it is the piece that came
      // off is not this function's business - a run holding the wrong katana casts perfectly well.
      if (!handsClear()) {
        return true;
      }

      // Nothing was taken off a hand, so an empty hand is the state this character started in
      if (!wanted.some((piece) => isHand(piece.layer))) {
        return true;
      }

      // The by-graphic search loses the properties and is still worth taking: an armed character
      // casts, and one holding nothing does not.
      if (options.rearm?.()) {
        return true;
      }

      // Armour that will not go back leaves a slower character; an empty hand leaves one that cannot
      // cast at all and cannot defend itself, which is the single thing here worth ending a run over.
      return false;
    },
  };
};
