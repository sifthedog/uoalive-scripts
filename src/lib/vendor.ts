import { collectIn, packContents } from './containers.js';

// The client parses a vendor gump for you, so selling never touches gump buttons. What it does not
// do is type the result: `VendorItem` is stubbed as `any` in types/classicuo.d.ts because its real
// shape is not shipped, so this is the shape the scripts rely on.
export interface VendorEntry {
  serial: number;
  name: string;
  amount?: number;
}

export interface SellRequestItem {
  serial: number;
  amount: number;
}

export interface SellGump {
  vendor: Mobile;
  items: VendorEntry[];
}

// Equality rather than a substring test - selling 'iron ingots' when asked for 'iron ingot' would
// be a different item, and a substring match would also hit 'dull copper iron ingot'
export const namedExactly =
  (name: string) =>
  (entry: VendorEntry): boolean =>
    (entry.name ?? '').toLowerCase() === name.toLowerCase();

// The same test against a list, so a sale for several items can be settled from the one gump the
// vendor already has open rather than saying 'vendor sell' once per name
export const namedAnyOf = (names: string[]) => {
  const wanted = new Set(names.map((name) => name.toLowerCase()));

  return (entry: VendorEntry): boolean => wanted.has((entry.name ?? '').toLowerCase());
};

// sendSellRequest only reads serial and amount, so trim the counts to leave `keep` behind
export const withKeepBack = (matches: VendorEntry[], keep: number): SellRequestItem[] => {
  let remaining = keep;
  const toSell: SellRequestItem[] = [];

  for (const item of matches) {
    const amount = item.amount ?? 1;

    if (remaining >= amount) {
      remaining -= amount;
      continue;
    }

    toSell.push({ serial: item.serial, amount: amount - remaining });
    remaining = 0;
  }

  return toSell;
};

export const totalOf = (entries: VendorEntry[]): number =>
  entries.reduce((sum, entry) => sum + (entry.amount ?? 1), 0);

// What is left of each offered stack, keyed by serial: a stack the vendor took entirely is gone
// from the pack and so absent from the map, while one it took part of keeps its serial and comes
// back smaller.
//
// The whole pack, at any depth. This used to read the top level only, on the assumption that a
// vendor is shown nothing below it - and a vendor that sells out of a bag turned that into a lie:
// an item offered from inside one was never at the top level, so it read as gone the instant it was
// offered and every refusal was reported as a sale. Counting where the goods actually are cannot
// make that mistake, whichever way the shard behaves.
const packLeft = (serials: Set<number>): Map<number, number> => {
  const left = new Map<number, number>();

  for (const item of collectIn(packContents(), (held) => serials.has(held.serial))) {
    left.set(item.serial, (left.get(item.serial) ?? 0) + (item.amount ?? 1));
  }

  return left;
};

// How many of the offered units actually left the pack, per offered stack. That the goods went is
// the only proof there is that a vendor took them: `sendSellRequest` answers whether the packet
// went out, not whether the sale landed, and a vendor that refuses does so in silence.
//
// Per stack rather than one total, because a single request may carry two names and 'the vendor
// took 25' does not say whose 25 they were.
//
// Matched by serial rather than by name, so nothing here needs tooltip data: a sold stack leaves
// the pack entirely and a partly sold one keeps its serial and drops its `amount`.
//
// Polled rather than slept through, the lesson boxes/drop.ts paid for. Reading the pack back too
// early only ever says the goods are still there, which costs a pass; it can never invent a sale.
export const waitForSaleBySerial = (
  offered: SellRequestItem[],
  timeoutMs: number,
  pollMs: number,
): Map<number, number> => {
  const serials = new Set(offered.map((item) => item.serial));
  let left = new Map<number, number>();
  let remaining = offered.reduce((sum, item) => sum + item.amount, 0);

  for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
    sleep(pollMs);
    left = packLeft(serials);
    remaining = [...left.values()].reduce((sum, amount) => sum + amount, 0);
  }

  // Floored at zero: a stack that came back bigger than it was offered - merged with one the player
  // picked up mid-sale - is not a negative sale, and this figure is what the run reports as sold
  return new Map(
    offered.map((item) => [item.serial, Math.max(0, item.amount - (left.get(item.serial) ?? 0))]),
  );
};

export const waitForSale = (
  offered: SellRequestItem[],
  timeoutMs: number,
  pollMs: number,
): number =>
  [...waitForSaleBySerial(offered, timeoutMs, pollMs).values()].reduce(
    (sum, taken) => sum + taken,
    0,
  );

// `prefix` keeps each script's log lines namespaced to itself
export const openSellGump = (prefix: string, timeoutMs: number): SellGump | undefined => {
  player.say('vendor sell');
  const data = Gump.waitForVendorGumpData(timeoutMs);

  if (!data) {
    log(`${prefix}: no vendor gump appeared - out of earshot?`);
    return undefined;
  }

  if (data.type !== 'sell') {
    log(`${prefix}: got a '${data.type}' gump instead of a sell gump`);
    return undefined;
  }

  return { vendor: data.vendor, items: (data.items ?? []) as VendorEntry[] };
};
