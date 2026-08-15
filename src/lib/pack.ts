import { contentsOf, packContents, type ItemPredicate } from './containers.js';

export type Counts = Map<string, number>;

export interface Change {
  key: string;
  delta: number;
}

// Keyed by graphic and hue together, because a recipe's output is told apart from the ingots it
// consumed by graphic, and coloured variants of the same item share a graphic.
export const countsByGraphic = (contents: Item[] | undefined = packContents()): Counts => {
  const counts: Counts = new Map();

  const walk = (items: Item[] | undefined) => {
    for (const item of items ?? []) {
      const key = `0x${item.graphic.toString(16)}/${item.hue ?? 0}`;
      counts.set(key, (counts.get(key) ?? 0) + (item.amount ?? 1));
      walk(contentsOf(item));
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

// How many of something the pack holds, sub-containers included, because the shard spends resources
// out of those too. A lower bound either way: an unopened container reports `contents: undefined`.
//
// Recursion goes through a second parameter rather than the exported call, because a plain item has
// no `contents` and passing undefined back into a defaulted parameter would restart at the backpack
// forever - the trap all three hand-written copies of this had to comment on.
export const totalMatching = (
  matches: ItemPredicate,
  contents: Item[] | undefined = packContents(),
): number =>
  (contents ?? []).reduce(
    (total, item) =>
      total +
      (matches(item) ? item.amount ?? 1 : 0) +
      totalMatching(matches, contentsOf(item) ?? []),
    0,
  );

export const describeDiff = (changes: Change[]): string =>
  changes.length
    ? changes.map(({ key, delta }) => `${key} ${delta > 0 ? '+' : ''}${delta}`).join(', ')
    : 'no change';
