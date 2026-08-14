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
import { beat, resetBeat } from './heartbeat.js';
import { now } from './memory.js';
import { isSaving, waitOutSave } from './save.js';
import {
  markDepleted,
  markNotHarvestable,
  markUnreachable,
  markUnusable,
  scanForTree,
} from './tree.js';
import { stepToward } from './walk.js';

// Learn the axe graphic from the one you start the script holding
rememberAxe(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded);

const minutesLeft = (until: number) => Math.max(1, Math.round((until - now()) / 60_000));

// Sliced rather than slept through in one go, so the client stays responsive and the guards still
// get a look in - a quarter of an hour is long enough to be killed standing there, and one long
// sleep would carry on regardless. Bounded by the wait it was asked for as well as by the clock:
// a clock that does not advance would otherwise turn this into a spin.
const idleUntil = (regrowsAt: number): void => {
  const wait = regrowsAt - now();
  if (wait <= 0) {
    return;
  }

  log(`lumberjack: everything in reach is regrowing, waiting ${minutesLeft(regrowsAt)}m`);

  const slices = Math.ceil(wait / IDLE_POLL);
  let since = 0;

  for (let slice = 0; slice < slices && now() < regrowsAt; slice++) {
    sleep(IDLE_POLL);
    since += IDLE_POLL;

    // Left to the loop to report and act on, so the wait has one way out and the run has one
    if (stopReason()) {
      return;
    }

    if (since >= IDLE_LOG_EVERY) {
      since = 0;
      log(`lumberjack: ${minutesLeft(regrowsAt)}m to go`);
    }
  }

  // This path reports on its own cadence, so start the next beat's interval from here rather than
  // letting one land on top of the line above
  resetBeat();
};

log(`lumberjack: ${logTotal()} logs in the pack to start, staying within ${describeBounds()}`);

let chopped = 0;
let unknown = 0;
let stop: string | undefined;

// The tally at the last progress line. Compared against rather than `chopped % LOG_EVERY`, which is
// a property of the count and not of the cycle: it stays true for every cycle that follows the
// twenty-fifth chop, so a run that then walks, waits or is refused reprints the same line each time.
let reported = 0;

// Consecutive refusals to swing, and cycles since the last chop landed. Neither branch used to
// count anything, which is how a run could stand still and silent for the whole cycle backstop.
let throttled = 0;
let sinceProgress = 0;

// Latched off the first time a haul frees nothing, so a missing animal costs one search rather
// than one per cycle for the rest of the run
let hauling = true;

// Steps spent on the tree we are currently walking to, reset when the target changes
let walkingTo: string | undefined;
let steps = 0;

// Closes every cycle that was meant to make progress: says the run is alive whatever branch it
// took, and counts the cycle against the watchdog. The regrow wait is the one path that does not
// come through here - it reports on its own cadence, and waiting for wood to grow back is the
// script working, not the script stuck.
const endCycle = (phase: string, cycle: number): void => {
  beat(phase, cycle, chopped);
  sinceProgress++;

  if (sinceProgress === STALL_WARN) {
    log(`lumberjack: ${STALL_WARN} cycles without a chop, last was '${phase}'`);
  }

  if (sinceProgress >= STALL_STOP) {
    stop = `no progress in ${STALL_STOP} cycles, last was '${phase}'`;
  }
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

    // A save freezes every part of a haul at once: the conversion is silent, the animal takes
    // nothing, and the weight does not move. Read as an ordinary result that latches hauling off
    // for the rest of the run - one unlucky ten seconds and every later load goes nowhere.
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

  // Nothing to chop now, but something is coming back: wait for it rather than ending a run that
  // only has to sit still to have a forest again
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
    // of them is written off the next is the same walk, so the step count should carry over rather
    // than start again. Two *different* trees taking turns as nearest still resets this, and no
    // per-target counter can catch that - the stall watchdog in endCycle is what bounds it.
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
      sinceProgress = 0;
      break;

    // A stump, not a dead tile: markDepleted times it out and the scan picks it up again later
    case 'empty':
      markDepleted(tree);
      unknown = 0;
      break;

    // The whole art is scenery, not just this tile, so ban the graphic and the rest of the
    // forest's copies of it stop being walked to one at a time
    case 'notTree':
      markNotHarvestable(tree.graphic);
      markUnusable(tree, 'is not harvestable');
      unknown = 0;
      break;

    // Already inside CHOP_RANGE, so this is the shard disagreeing about the range rather than a
    // walk that fell short. Treat the tile as unreachable instead of swinging at it again.
    case 'tooFar':
      markUnusable(tree, `is out of reach at ${tree.distance} tiles`);
      unknown = 0;
      break;

    // Line of sight, so walking closer would not help and neither would waiting - something is
    // simply in the way. Without this the tile reads as an unreadable outcome, is picked again by
    // the very next scan, and five of them in a row end the run.
    case 'notSeen':
      markUnusable(tree, 'is not in line of sight');
      unknown = 0;
      break;

    case 'wornOut':
      log('lumberjack: axe worn out, swapping');
      unknown = 0;
      break;

    // Nothing was learned about the tree and nothing went wrong: the shard was busy. The counters
    // are reset rather than merely left alone, because whatever they had accumulated was measured
    // against a server that was not answering.
    // Sitting out a save is the script working, not the script stuck, so the stall watchdog is
    // reset along with the rest: a shard that saves often would otherwise walk a run to STALL_STOP
    // a save at a time, and the regrow wait is already excused on exactly this reasoning.
    case 'saving':
      waitOutSave();
      unknown = 0;
      throttled = 0;
      sinceProgress = 0;
      break;

    // The one branch that used to say nothing and count nothing. A fixed 600ms retry is shorter
    // than the harvest delay on most shards, so the swing that was refused re-armed the very timer
    // it was waiting on - silently, standing still, for as long as the cycle backstop allowed.
    // Back off further each time instead, and give up rather than spin.
    case 'throttled':
      throttled++;

      // A refusal is a read outcome, so it clears the unreadable count the way every other named
      // branch does. Left standing, a shard alternating refusals with silence ends the run on
      // MAX_UNKNOWN without ever having produced five unreadable cycles in a row.
      unknown = 0;
      log(`lumberjack: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(Math.min(THROTTLE_BACKOFF * throttled, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // A cursor that never opened, with an axe demonstrably in hand, is the shard declining to start
    // the swing rather than an empty hand - on a live mining run that was a third of them. Backed
    // off like a throttle, but still counted: five in a row with nothing else happening is a stuck
    // run whatever the cause.
    case 'noCursor':
      unknown++;
      sleep(THROTTLE_BACKOFF);
      break;

    default:
      unknown++;
      log(`lumberjack: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
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
