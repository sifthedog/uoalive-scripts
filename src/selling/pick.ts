import { hex } from '../lib/entity.js';
import { OPL_TIMEOUT } from './config.js';

export interface Picked {
  serial: number;
  name: string;

  // The art, which is how sell-watch counts the pack: a graphic is on the item already, while a
  // name may have to be asked for - and a watch that runs for hours cannot afford to go blind when
  // the tooltips stop answering. The sale still matches by name, because the gump only has names.
  graphic: number;
}

// `TargetInfo` is stubbed as `any` in types/classicuo.d.ts because the client ships no type for it.
// Observed on the shard as `{serial, graphic, x, y, z, hue}` - a click on a copper key answered
// `{serial: 1098445366, graphic: 4110, x: 115, y: 67, z: 0, hue: 0}`
interface TargetInfo {
  serial?: number;
  graphic?: number;
}

// Names are empty until the client has tooltip data, and an item you have never hovered is exactly
// that case, so the tooltip comes first. Both lookups key off the serial that was just clicked;
// `target.last` is deliberately not consulted, because `query()` leaves it on the previous pick
const resolveName = (serial: number): string => {
  const fromTooltip = (client.queryItemOPL(serial, OPL_TIMEOUT)?.name ?? '').trim();

  return fromTooltip || (client.findObject(serial)?.name ?? '').trim();
};

export const pickItem = (): Picked | undefined => {
  // A cursor left open by whatever ran last would swallow this query, and every other targeting
  // site in the repo brackets itself the same way - smelt.ts, dig.ts, chop.ts, lib/tool.ts
  target.cancel();

  log('sell: target the item you want to sell');

  // The serial has to come off the return value: `query()` does not move `target.lastSerial`, so
  // comparing that before and after reads a re-run against the same item as a cancelled cursor
  const info = target.query() as TargetInfo | undefined;
  const serial = info?.serial ?? 0;

  if (!serial) {
    // A cancelled pick can still leave the cursor up, and the hoist that follows a successful one
    // is all double-clicks: a live cursor would spend them as target clicks instead
    target.cancel();
    log('sell: nothing targeted', info);
    return undefined;
  }

  const name = resolveName(serial);
  if (!name) {
    log(`sell: no name for ${hex(serial)}, the vendor list can only be matched by name`);
    return undefined;
  }

  // The query carries it on this shard, but it is `any` and undocumented either way, so fall back
  // to the object the same way the name does. Zero means 'no art', which matches nothing rather
  // than matching everything - the safe direction for a counter that decides when to sell.
  const graphic = info?.graphic ?? client.findObject(serial)?.graphic ?? 0;

  return { serial, name, graphic };
};
