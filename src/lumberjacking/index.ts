import { backoffFor, createIdleWait, createStallWatch } from '../lib/loop.js';
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
import {
  markDepleted,
  markNotHarvestable,
  markUnreachable,
  markUnusable,
  scanForTree,
} from './tree.js';
import { stepToward } from './walk.js';

rememberAxe(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded);

const idleUntil = createIdleWait({
  prefix: 'lumberjack',
  waitingFor: 'everything in reach is regrowing',
  pollMs: IDLE_POLL,
  logEveryMs: IDLE_LOG_EVERY,
  stopReason,
  onDone: resetBeat,
});

log(`lumberjack: ${logTotal()} logs in the pack to start, staying within ${describeBounds()}`);

let chopped = 0;
let unknown = 0;
let stop: string | undefined;

// Compared against rather than `chopped % LOG_EVERY`, which is a property of the count and not of
// the cycle - so it stays true for every cycle after the twenty-fifth chop.
let reported = 0;

let throttled = 0;

// Counted apart from `unknown`, which it used to share: a refusal is not an outcome the script
// failed to read, and spending that budget on one ended a live mining run in fifteen seconds with a
// tool in hand.
let noCursor = 0;

// Latched off the first time a haul frees nothing, so a missing animal costs one search rather than
// one per cycle for the rest of the run
let hauling = true;

// Steps spent on the tree currently being walked to, reset when the target changes
let walkingTo: string | undefined;
let steps = 0;

const stall = createStallWatch({
  prefix: 'lumberjack',
  without: 'cycles without a chop',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

const endCycle = (phase: string, cycle: number): void => {
  stall.endCycle(phase, cycle, chopped);
  stop ??= stall.reason();
};

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  if (!equipAxe()) {
    stop = 'no axe';
    break;
  }

  // Fires below the guards' overweight threshold, so there is still room to work in. The boards
  // are made first: an unconvertible hue still gets hauled, but a convertible one travels lighter.
  if (hauling && overweight(HAUL_BUFFER)) {
    const weightBefore = player.weight;

    makeBoards();
    unload();

    // A save freezes every part of a haul at once, and read as an ordinary result it latches
    // hauling off for the rest of the run.
    if (isSaving()) {
      waitOutSave();
    } else if (player.weight >= weightBefore) {
      hauling = false;
      log('lumberjack: hauling freed nothing, carrying on until overweight');
    }

    endCycle('hauling', cycle);
    sleep(STEP_DELAY);
    continue;
  }

  const { tree, regrowsAt } = scanForTree();

  if (!tree) {
    if (regrowsAt === undefined) {
      stop = 'no tree in range';
      break;
    }

    idleUntil(regrowsAt);
    continue;
  }

  if (tree.distance > CHOP_RANGE) {
    // Coarser than the block map's key on purpose: several statics stand on one tile, and once one
    // is written off the next is the same walk. Two *different* trees taking turns as nearest still
    // reset it - the stall watchdog in endCycle is what bounds that.
    const key = `${tree.x},${tree.y}`;
    if (key !== walkingTo) {
      walkingTo = key;
      steps = 0;
    }

    // Blocked or out of patience: set the tile aside, or the next scan picks the same tree again
    if (!stepToward(tree) || ++steps > MAX_STEPS) {
      markUnreachable(tree);
      walkingTo = undefined;
    }

    endCycle('walking', cycle);
    continue;
  }

  walkingTo = undefined;

  const outcome = chopOnce(tree, axeSerial());

  switch (outcome) {
    case 'chopped':
      chopped++;
      unknown = 0;
      throttled = 0;
      stall.progressed();
      break;

    // A stump, not a dead tile: markDepleted times it out and the scan picks it up again later
    case 'empty':
      markDepleted(tree);
      unknown = 0;
      break;

    // The whole art is scenery, not just this tile, so ban the graphic rather than walking to the
    // forest's copies of it one at a time
    case 'notTree':
      markNotHarvestable(tree.graphic);
      markUnusable(tree, 'is not harvestable');
      unknown = 0;
      break;

    // Already inside CHOP_RANGE, so the shard disagrees about the range rather than the walk having
    // fallen short
    case 'tooFar':
      markUnusable(tree, `is out of reach at ${tree.distance} tiles`);
      unknown = 0;
      break;

    // Line of sight: walking closer would not help and neither would waiting. Without this the tile
    // reads as an unreadable outcome, is picked again by the next scan, and five end the run.
    case 'notSeen':
      markUnusable(tree, 'is not in line of sight');
      unknown = 0;
      break;

    case 'wornOut':
      log('lumberjack: axe worn out, swapping');
      unknown = 0;
      break;

    // The counters are reset rather than left alone, because whatever they had accumulated was
    // measured against a server that was not answering. The stall watchdog goes with them: a shard
    // that saves often would otherwise walk a run to STALL_STOP a save at a time.
    case 'saving':
      waitOutSave();
      unknown = 0;
      throttled = 0;
      stall.progressed();
      break;

    case 'throttled':
      throttled++;

      // A refusal is a read outcome, so it clears the unreadable count: left standing, a shard
      // alternating refusals with silence ends the run on MAX_UNKNOWN without ever producing five
      // unreadable cycles in a row.
      unknown = 0;
      log(`lumberjack: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // With an axe demonstrably in hand this is the shard declining to start the swing, which on a
    // live mining run was a third of them. chopOnce has already looked for a reason, so this is a
    // refusal with nothing said about it - backed off like one, on a budget of its own.
    case 'noCursor':
      noCursor++;
      log(`lumberjack: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
      sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (noCursor >= MAX_NO_CURSOR) {
        stop = 'the shard never opened a target cursor';
      }
      break;

    default:
      unknown++;
      log(`lumberjack: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
  }

  // Done here rather than inside each branch the way `unknown` is: every branch but one clears it,
  // and one added later would have to remember to.
  if (outcome !== 'noCursor') {
    noCursor = 0;
  }

  if (unknown >= MAX_UNKNOWN) {
    stop = `${MAX_UNKNOWN} unreadable outcomes in a row`;
    break;
  }

  if (chopped >= reported + LOG_EVERY) {
    reported = chopped;
    log(`lumberjack: ${chopped} chops, ${logTotal()} logs, ${player.weight}/${player.weightMax}`);
  }

  endCycle(outcome ?? 'unknown', cycle);
  sleep(STEP_DELAY);
}

// A run that ended for some other reason - no trees left, an unreadable outcome - still finishes
// with boards on the animal rather than logs in the pack
makeBoards();
if (hauling) {
  unload();
}

// Chops rather than a log delta: hauled wood has left the pack, so the pack cannot total the run
log(`lumberjack: ${chopped} chops, ${logTotal()} logs still in the pack`);
exit(`lumberjack: ${stop ?? `hit the ${MAX_CYCLES} cycle backstop`}`);
