import { OPL_TIMEOUT } from './config.js';

export interface Picked {
  serial: number;
  name: string;
}

// `TargetInfo` is stubbed as `any` in types/classicuo.d.ts because the client ships no type for it.
// Observed on the shard as `{serial, graphic, x, y, z, hue}` - a click on a copper key answered
// `{serial: 1098445366, graphic: 4110, x: 115, y: 67, z: 0, hue: 0}`
interface TargetInfo {
  serial?: number;
}

// Names are empty until the client has tooltip data, and an item you have never hovered is exactly
// that case, so the tooltip comes first. Both lookups key off the serial that was just clicked;
// `target.last` is deliberately not consulted, because `query()` leaves it on the previous pick
const resolveName = (serial: number): string => {
  const fromTooltip = (client.queryItemOPL(serial, OPL_TIMEOUT)?.name ?? '').trim();

  return fromTooltip || (client.findObject(serial)?.name ?? '').trim();
};

export const pickItem = (): Picked | undefined => {
  log('sell: target the item you want to sell');

  // The serial has to come off the return value: `query()` does not move `target.lastSerial`, so
  // comparing that before and after reads a re-run against the same item as a cancelled cursor
  const info = target.query() as TargetInfo | undefined;
  const serial = info?.serial ?? 0;

  if (!serial) {
    log('sell: nothing targeted', info);
    return undefined;
  }

  const name = resolveName(serial);
  if (!name) {
    // Serials come back as signed 32-bit ints, so a plain toString(16) yields "0x-3266af2f"
    const label = (serial >>> 0).toString(16);
    log(`sell: no name for 0x${label}, the vendor list can only be matched by name`);
    return undefined;
  }

  return { serial, name };
};
