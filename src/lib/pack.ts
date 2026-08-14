export type Counts = Map<string, number>;

export interface Change {
  key: string;
  delta: number;
}

// Keyed by graphic and hue together, because a recipe's output is told apart from the ingots it
// consumed by graphic, and coloured variants of the same item share a graphic.
export const countsByGraphic = (
  contents: Item[] | undefined = player.backpack?.contents,
): Counts => {
  const counts: Counts = new Map();

  const walk = (items: Item[] | undefined) => {
    for (const item of items ?? []) {
      const key = `0x${item.graphic.toString(16)}/${item.hue ?? 0}`;
      counts.set(key, (counts.get(key) ?? 0) + (item.amount ?? 1));
      walk(item.contents);
    }
  };

  walk(contents);
  return counts;
};

// Only what changed, so a trial press reports the item it made rather than the whole pack
export const diffCounts = (before: Counts, after: Counts): Change[] => {
  const changes: Change[] = [];

  for (const [key, total] of after) {
    const delta = total - (before.get(key) ?? 0);
    if (delta !== 0) {
      changes.push({ key, delta });
    }
  }

  for (const [key, total] of before) {
    if (!after.has(key)) {
      changes.push({ key, delta: -total });
    }
  }

  return changes;
};

export const describeDiff = (changes: Change[]): string =>
  changes.length
    ? changes.map(({ key, delta }) => `${key} ${delta > 0 ? '+' : ''}${delta}`).join(', ')
    : 'no change';
