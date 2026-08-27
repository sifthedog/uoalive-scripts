import { hex } from '../lib/entity.js';
import { createScan, createTileStore, type Tile } from '../lib/tiles.js';
import { reachableFromBounds } from './bounds.js';
import {
  CHOP_RANGE,
  NOT_TREE_GRAPHICS,
  REGROW_DELAY,
  SCAN_RADIUS,
  TREE_GRAPHICS,
  UNREACHABLE_DELAY,
} from './config.js';
import { memory } from './memory.js';

export type { Tile };

export interface Tree extends Tile {
  distance: number;
}

export interface Scan {
  tree?: Tree;

  // The soonest a tile that is only cooling down comes back. Undefined when nothing is waiting to
  // regrow, which is what tells an idle wait apart from a wood with nothing left in it.
  regrowsAt?: number;
}

// getStatic reads the client's own tiledata, so the answer never changes. The scan asks about the
// same handful of graphics hundreds of times a cycle, so remember them.
const known = new Map<number, boolean>();

// Overrides first, because both seed sets ship empty - unlike mining's, which ships full and has to
// ask its bans first or a learned refusal would be silently outranked by the seed
export const isTree = (graphic: number): boolean => {
  if (TREE_GRAPHICS.has(graphic)) {
    return true;
  }
  if (NOT_TREE_GRAPHICS.has(graphic) || memory().notTree.has(graphic)) {
    return false;
  }

  const remembered = known.get(graphic);
  if (remembered !== undefined) {
    return remembered;
  }

  const name = client.getStatic(graphic)?.name ?? '';
  const matches = /tree/i.test(name);
  known.set(graphic, matches);

  return matches;
};

const store = /* @__PURE__ */ createTileStore<Tile>({
  label: 'tree',
  blocked: () => memory().blocked,
  depletedFor: REGROW_DELAY,
  unreachableFor: UNREACHABLE_DELAY,
  depleted: 'is out of wood',
});

export const markDepleted = store.markDepleted;
export const markUnreachable = store.markUnreachable;
export const markUnusable = store.markUnusable;

// About the graphic, not the tile: the tiledata calls a whole family of statics a tree, and only the
// trunk is harvestable. Banning the graphic drops every other tile of that art in one go.
export const markNotHarvestable = (graphic: number): void => {
  const { notTree } = memory();

  if (notTree.has(graphic)) {
    return;
  }

  notTree.add(graphic);
  log(`tree: ${hex(graphic)} cannot be chopped, skipping that art from here on`);
};

const scan = /* @__PURE__ */ createScan<Tile>({
  label: 'scanForTree',
  radius: SCAN_RADIUS,
  blocked: () => memory().blocked,

  // A tree is a static, so land is skipped outright rather than asked about
  skipLand: true,
  matches: (graphic) => isTree(graphic),

  // Trees outside the box are still fair game when a legal standing tile is within CHOP_RANGE;
  // filtered here rather than picked, walked at, refused and written off MAX_STEPS later.
  reach: (tree) => (reachableFromBounds(tree.x, tree.y, CHOP_RANGE) ? 0 : undefined),

  describe: (tree) => `'${client.getStatic(tree.graphic)?.name ?? '?'}'`,
});

export const scanForTree = (): Scan => {
  const { found, readyAt } = scan();

  return { tree: found, regrowsAt: readyAt };
};
