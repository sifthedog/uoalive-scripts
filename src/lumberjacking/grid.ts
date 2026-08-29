import { createGrid } from '../lib/grid.js';
import { inBounds } from './bounds.js';
import {
  MAX_CLIMB,
  MAX_ROUTE_CELLS,
  MAX_ROUTE_NODES,
  MAX_TREE_STEPS,
  PLAYER_HEIGHT,
  ROUTE_RADIUS,
  STEP_HEADROOM,
} from './config.js';

export const grid = /* @__PURE__ */ createGrid({
  radius: ROUTE_RADIUS,
  maxSteps: MAX_TREE_STEPS,
  maxNodes: MAX_ROUTE_NODES,
  maxCells: MAX_ROUTE_CELLS,
  climb: MAX_CLIMB,
  height: PLAYER_HEIGHT,
  headroom: STEP_HEADROOM,

  // Mining roams and passes nothing here; a route that left the box would be refused a step at a
  // time by allowedStep and the tree written off as unreachable.
  passable: inBounds,
});
