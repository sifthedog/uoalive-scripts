import { hex } from '../lib/entity.js';
import { MAX_PICKS, OPL_TIMEOUT } from './config.js';

export interface Picked {
  serial: number;
  name: string;

  // How sell-watch counts the pack: a graphic is on the item already, while a name may have to be
  // asked for, and a watch that runs for hours cannot go blind when the tooltips stop answering.
  // The sale still matches by name, because the gump only has names.
  graphic: number;
}

// `TargetInfo` is stubbed as `any` in types/classicuo.d.ts because the client ships no type for it.
// Observed on the shard as `{serial, graphic, x, y, z, hue}`.
interface TargetInfo {
  serial?: number;
  graphic?: number;
}

// Names are empty until the client has tooltip data, which an item you have never hovered is. Both
// lookups key off the serial just clicked - `target.last` is left alone, because `query()` leaves it
// on the previous pick.
const resolveName = (serial: number): string => {
  const fromTooltip = (client.queryItemOPL(serial, OPL_TIMEOUT)?.name ?? '').trim();

  return fromTooltip || (client.findObject(serial)?.name ?? '').trim();
};

// One click, or nothing for a cancelled cursor - the only sign the client gives that ESC was
// pressed. There is no key event and no cancel callback in the API, so this is indistinguishable
// from a click that resolved to nothing, and both mean the same thing: stop asking.
const clicked = (prefix: string): TargetInfo | undefined => {
  // A cursor left open by whatever ran last would swallow this query
  target.cancel();

  // The serial has to come off the return value: `query()` does not move `target.lastSerial`, so
  // comparing that before and after reads a second pick of the same item as a cancelled cursor
  const info = target.query() as TargetInfo | undefined;

  if (!(info?.serial ?? 0)) {
    // A cancelled pick can still leave the cursor up, and a live one would spend the double-clicks
    // and gumps that follow a selection as target clicks instead
    target.cancel();
    log(`${prefix}: nothing targeted`, info);
    return undefined;
  }

  return info;
};

// Nothing means the click landed on something nobody will name - worth skipping over, not worth
// ending the selection for.
const describe = (prefix: string, info: TargetInfo): Picked | undefined => {
  const serial = info.serial ?? 0;
  const name = resolveName(serial);

  if (!name) {
    log(`${prefix}: no name for ${hex(serial)}, the vendor list can only be matched by name`);
    return undefined;
  }

  // The query carries it on this shard, but it is `any` and undocumented, so fall back to the object
  // the way the name does. Zero means 'no art', which matches nothing rather than everything.
  const graphic = info.graphic ?? client.findObject(serial)?.graphic ?? 0;

  return { serial, name, graphic };
};

// Click item after item, ESC to finish. Empty means the first cursor was cancelled, which callers
// treat as 'nothing to do' rather than a fault.
//
// Deduplicated by name, because that is what the sale matches on: offering one name twice would trim
// it to KEEP twice over.
export const pickItems = (prefix: string): Picked[] => {
  const picks: Picked[] = [];
  const seen = new Set<string>();

  log(`${prefix}: target the items you want to sell, ESC when done`);

  let asked = 0;

  for (; asked < MAX_PICKS; asked++) {
    const info = clicked(prefix);

    if (!info) {
      break;
    }

    const picked = describe(prefix, info);

    // Skipped rather than returned, so an item the client cannot name yet costs the click it was on
    // and nothing more
    if (!picked) {
      continue;
    }

    const name = picked.name.toLowerCase();

    if (seen.has(name)) {
      log(`${prefix}: '${picked.name}' is already on the list`);
      continue;
    }

    seen.add(name);
    picks.push(picked);
    log(`${prefix}:   ${picks.length}. ${picked.name}`);
  }

  // Only reachable without an ESC, so the cursor is closed here the way every other exit does it
  if (asked === MAX_PICKS) {
    log(`${prefix}: ${MAX_PICKS} clicks is as many as one run takes`);
    target.cancel();
  }

  return picks;
};
