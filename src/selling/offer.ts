import {
  withKeepBack as trimTo,
  type SellRequestItem,
  type VendorEntry,
} from '../lib/vendor.js';
import { KEEP } from './config.js';

export type { SellRequestItem, VendorEntry };

// KEEP is per item - 'leave this many behind' means ten of each, not ten between them - so a sale
// carrying several names has to be grouped before it is trimmed. Order follows the gump, so the
// request lists entries in the order the vendor did.
export const withKeepBack = (matches: VendorEntry[]): SellRequestItem[] => {
  const byName = new Map<string, VendorEntry[]>();

  for (const entry of matches) {
    const name = (entry.name ?? '').toLowerCase();
    const group = byName.get(name);

    if (group) {
      group.push(entry);
      continue;
    }

    byName.set(name, [entry]);
  }

  const order = new Map(matches.map((entry, index) => [entry.serial, index]));

  return [...byName.values()]
    .flatMap((group) => trimTo(group, KEEP))
    .sort((a, b) => (order.get(a.serial) ?? 0) - (order.get(b.serial) ?? 0));
};
