import { queryOPL } from './opl.js';

export interface Picked {
  serial: number;
  name: string;
  graphic: number;
  hue: number;
}

// `TargetInfo` is stubbed as `any` in types/classicuo.d.ts because the client ships no type for it.
// Observed on the shard as `{serial, graphic, x, y, z, hue}`.
interface TargetInfo {
  serial?: number;
  graphic?: number;
  hue?: number;
}

export interface PickOneOptions {
  prefix: string;
  prompt: string;
  oplTimeout: number;
}

export interface PickManyOptions extends PickOneOptions {
  maxPicks: number;

  // undefined skips the pick without ending the selection, for a click the caller cannot key on
  keyOf: (picked: Picked) => string | undefined;

  label?: (picked: Picked) => string;
}

// Names are empty until the client has tooltip data, which an item you have never hovered is. Both
// lookups key off the serial just clicked - `target.last` is left alone, because `query()` leaves it
// on the previous pick.
const resolveName = (serial: number, oplTimeout: number, prefix: string): string => {
  const fromTooltip = (queryOPL(serial, oplTimeout, prefix)?.name ?? '').trim();

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

// The query carries the art and the hue on this shard, but it is `any` and undocumented, so both
// fall back to the object. Zero art means 'nothing known', which matches nothing rather than
// everything.
const describe = (info: TargetInfo, oplTimeout: number, prefix: string): Picked => {
  const serial = info.serial ?? 0;
  const found = client.findObject(serial);

  return {
    serial,
    name: resolveName(serial, oplTimeout, prefix),
    graphic: info.graphic ?? found?.graphic ?? 0,
    hue: info.hue ?? found?.hue ?? 0,
  };
};

export const pickOne = ({ prefix, prompt, oplTimeout }: PickOneOptions): Picked | undefined => {
  log(`${prefix}: ${prompt}`);

  const info = clicked(prefix);

  return info && describe(info, oplTimeout, prefix);
};

// Click item after item, ESC to finish. Empty means the first cursor was cancelled, which callers
// treat as a choice rather than a fault.
export const pickMany = ({
  prefix,
  prompt,
  maxPicks,
  oplTimeout,
  keyOf,
  label,
}: PickManyOptions): Picked[] => {
  const picks: Picked[] = [];
  const seen = new Set<string>();
  const name = label ?? ((picked: Picked) => picked.name);

  log(`${prefix}: ${prompt}`);

  let asked = 0;

  for (; asked < maxPicks; asked++) {
    const info = clicked(prefix);

    if (!info) {
      break;
    }

    const picked = describe(info, oplTimeout, prefix);
    const key = keyOf(picked);

    if (key === undefined) {
      continue;
    }

    if (seen.has(key)) {
      log(`${prefix}: '${name(picked)}' is already on the list`);
      continue;
    }

    seen.add(key);
    picks.push(picked);
    log(`${prefix}:   ${picks.length}. ${name(picked)}`);
  }

  // Only reachable without an ESC, so the cursor is closed here the way every other exit does it
  if (asked === maxPicks) {
    log(`${prefix}: ${maxPicks} clicks is as many as one run takes`);
    target.cancel();
  }

  return picks;
};
