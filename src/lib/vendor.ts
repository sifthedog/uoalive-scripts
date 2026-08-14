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

// Only the top level of the pack, because that is all the vendor was ever shown
const looseTotal = (serials: Set<number>): number =>
  (player.backpack?.contents ?? [])
    .filter((item) => serials.has(item.serial))
    .reduce((sum, item) => sum + (item.amount ?? 1), 0);

// How many of the offered units actually left the pack, which is the only proof there is that a
// vendor took them: `sendSellRequest` answers whether the packet went out, not whether the sale
// landed, and a vendor that refuses does so in silence.
//
// Matched by serial rather than by name, so nothing here needs tooltip data: a sold stack leaves
// the pack entirely and a partly sold one keeps its serial and drops its `amount`.
//
// Polled rather than slept through, the lesson boxes/drop.ts paid for. Reading the pack back too
// early only ever says the goods are still there, which costs a pass; it can never invent a sale.
export const waitForSale = (
  offered: SellRequestItem[],
  timeoutMs: number,
  pollMs: number,
): number => {
  const serials = new Set(offered.map((item) => item.serial));
  const total = offered.reduce((sum, item) => sum + item.amount, 0);
  let remaining = total;

  for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
    sleep(pollMs);
    remaining = looseTotal(serials);
  }

  return total - remaining;
};

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
