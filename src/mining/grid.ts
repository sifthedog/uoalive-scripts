import { createGrid } from '../lib/grid.js';
import {
  MAX_CLIMB,
  MAX_ROUTE_CELLS,
  MAX_ROUTE_NODES,
  MAX_VEIN_STEPS,
  PLAYER_HEIGHT,
  ROUTE_RADIUS,
  STEP_HEADROOM,
} from './config.js';

export const grid = /* @__PURE__ */ createGrid({
  radius: ROUTE_RADIUS,
  maxSteps: MAX_VEIN_STEPS,
  maxNodes: MAX_ROUTE_NODES,
  maxCells: MAX_ROUTE_CELLS,
  climb: MAX_CLIMB,
  height: PLAYER_HEIGHT,
  headroom: STEP_HEADROOM,
});
