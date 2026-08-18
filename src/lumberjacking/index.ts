import { runHarvest, type Handled, type Interlude } from '../lib/harvest.js';
import { createIdleWait, createStallWatch } from '../lib/loop.js';
import { createApproach } from '../lib/tiles.js';
import { overweight } from '../lib/weight.js';
import { axeSerial, equipAxe, rememberAxe } from './axe.js';
import { makeBoards } from './boards.js';
import { describeBounds } from './bounds.js';
import { chopOnce, logTotal } from './chop.js';
import {
  CHOP_RANGE,
  HAUL_BUFFER,
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_STEPS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { unload } from './haul.js';
import { heartbeat, resetBeat } from './heartbeat.js';
import { isSaving, waitOutSave } from './save.js';
import { watchForTrouble } from './threat.js';
import {
  markDepleted,
  markNotHarvestable,
  markUnreachable,
  markUnusable,
  scanForTree,
  type Tree,
} from './tree.js';
import { stepToward } from './walk.js';

rememberAxe(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded);

const idleUntil = createIdleWait({
  prefix: 'lumberjack',
  waitingFor: 'everything in reach is regrowing',
  pollMs: IDLE_POLL,
  logEveryMs: IDLE_LOG_EVERY,
  stopReason,
  watch: watchForTrouble,
  onDone: resetBeat,
});

log(`lumberjack: ${logTotal()} logs in the pack to start, staying within ${describeBounds()}`);

// Latched off the first time a haul frees nothing, so a missing animal costs one search rather than
// one per cycle for the rest of the run
let hauling = true;

// Fires below the guards' overweight threshold, so there is still room to work in. The boards are
// made first: an unconvertible hue still gets hauled, but a convertible one travels lighter.
const haulForRoom = (): Interlude => {
  if (!hauling || !overweight(HAUL_BUFFER)) {
    return undefined;
  }

  const weightBefore = player.weight;

  makeBoards();
  unload();

  // A save freezes every part of a haul at once, and read as an ordinary result it latches hauling
  // off for the rest of the run.
  if (isSaving()) {
    waitOutSave();
  } else if (player.weight >= weightBefore) {
    hauling = false;
    log('lumberjack: hauling freed nothing, carrying on until overweight');
  }

  return { phase: 'hauling' };
};

const handle = (outcome: string, tree?: Tree): Handled => {
  if (!tree) {
    return undefined;
  }

  switch (outcome) {
    // A stump, not a dead tile: markDepleted times it out and the scan picks it up again later
    case 'empty':
      markDepleted(tree);

      return {};

    // The whole art is scenery, not just this tile, so ban the graphic rather than walking to the
    // forest's copies of it one at a time
    case 'notTree':
      markNotHarvestable(tree.graphic);
      markUnusable(tree, 'is not harvestable');

      return {};

    // Already inside CHOP_RANGE, so the shard disagrees about the range rather than the walk having
    // fallen short
    case 'tooFar':
      markUnusable(tree, `is out of reach at ${tree.distance} tiles`);

      return {};

    // Line of sight: walking closer would not help and neither would waiting. Without this the tile
    // reads as an unreadable outcome, is picked again by the next scan, and five end the run.
    case 'notSeen':
      markUnusable(tree, 'is not in line of sight');

      return {};

    default:
      return undefined;
  }
};

runHarvest<Tree & { distance: number }>({
  prefix: 'lumberjack',
  landed: 'chopped',
  toolName: 'axe',

  stopReason,
  watch: watchForTrouble,
  equipTool: equipAxe,
  relieve: haulForRoom,
  waitOutSave,

  approach: createApproach<Tree>({
    // Renamed rather than shared: 'tree' and 'regrowsAt' are what this folder's tests read
    scan: () => {
      const { tree, regrowsAt } = scanForTree();

      return { found: tree, readyAt: regrowsAt };
    },

    range: CHOP_RANGE,
    maxSteps: MAX_STEPS,
    step: stepToward,
    markUnreachable,
    idleUntil,
    nothingFound: () => 'no tree in range',
  }),

  harvest: (tree) => (tree ? chopOnce(tree, axeSerial()) : undefined),

  handle,

  progress: (chopped) => `${chopped} chops, ${logTotal()} logs`,

  finish: (chopped) => {
    // A run that ended for some other reason - no trees left, an unreadable outcome - still finishes
    // with boards on the animal rather than logs in the pack
    makeBoards();

    if (hauling) {
      unload();
    }

    // Chops rather than a log delta: hauled wood has left the pack, so the pack cannot total the run
    log(`lumberjack: ${chopped} chops, ${logTotal()} logs still in the pack`);
  },

  stall: createStallWatch({
    prefix: 'lumberjack',
    without: 'cycles without a chop',
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat,
  }),

  timings: {
    stepDelay: STEP_DELAY,
    maxCycles: MAX_CYCLES,
    maxUnknown: MAX_UNKNOWN,
    maxThrottled: MAX_THROTTLED,
    maxNoCursor: MAX_NO_CURSOR,
    logEvery: LOG_EVERY,
    throttleBackoff: THROTTLE_BACKOFF,
    throttleBackoffMax: THROTTLE_BACKOFF_MAX,
  },
});
