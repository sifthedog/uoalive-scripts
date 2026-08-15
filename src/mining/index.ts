import { describeItem } from '../lib/entity.js';
import { backoffFor, createIdleWait, createStallWatch } from '../lib/loop.js';
import { overweight } from '../lib/weight.js';
import {
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_STEPS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  MINE_RANGE,
  NOTHING_NEARBY_HINT,
  SCAN_RADIUS,
  SURVEY_ARTS,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { digOnce } from './dig.js';
import { stopReason } from './guards.js';
import { heartbeat, resetBeat } from './heartbeat.js';
import { dismount } from './mount.js';
import { groupOres, oreTotal, waitForOre } from './ore.js';
import { equipPickaxe, pickaxeSerial, rememberPickaxe } from './pickaxe.js';
import { waitOutSave } from './save.js';
import { retryUnsmeltable, smeltAll } from './smelt.js';
import { reportTerrain } from './survey.js';
import {
  markAreaDepleted,
  markDepleted,
  markNotMineable,
  markUnreachable,
  markUnusable,
  scanForVein,
} from './vein.js';
import { stepToward } from './walk.js';

rememberPickaxe(player.equippedItems.oneHanded);

const idleUntil = createIdleWait({
  prefix: 'mining',
  waitingFor: 'everything in reach is worked out',
  pollMs: IDLE_POLL,
  logEveryMs: IDLE_LOG_EVERY,
  stopReason,
  onDone: resetBeat,
});

// No buffer: ore travels as ore until it cannot travel at all.
const tooHeavy = (): boolean => overweight();

// A spot running dry is the cheapest moment to turn a pack of ore into a pocketful of ingots: the
// character is about to walk off anyway. Neither call costs anything when there is nothing to do.
const groupAndSmelt = (): void => {
  groupOres();
  smeltAll();
};

log(`mining: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);

// A run that stops on its first cycle looks from the outside like one that never started, so the
// three things that end one that early are said out loud first.
log(
  `mining: mounted ${player.equippedItems.mount ? 'yes' : 'no'}, ` +
    `hand ${describeItem(player.equippedItems.oneHanded)}, ` +
    `weight ${player.weight}/${player.weightMax}`,
);

let mined = 0;
let unknown = 0;
let stop: string | undefined;

// Compared against rather than `mined % LOG_EVERY`, which is a property of the count and not of the
// cycle - so it stays true for every cycle after the twenty-fifth swing.
let reported = 0;

let throttled = 0;

// Counted apart from `unknown`, which it used to share: a refusal is not an outcome the script
// failed to read, and spending that budget on one ended a run in fifteen seconds with a pickaxe
// plainly in hand.
let noCursor = 0;

// Spots in a row the shard said had nothing in them. A few is roaming; a lot in a row is
// ORE_TILE_GRAPHICS matching ground that carries no ore, which looks identical from the outside.
let barren = 0;

// Steps spent on the vein currently being walked to, reset when the target changes
let walkingTo: string | undefined;
let steps = 0;

const stall = createStallWatch({
  prefix: 'mining',
  without: 'cycles without a swing landing',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

const endCycle = (phase: string, cycle: number): void => {
  stall.endCycle(phase, cycle, mined);
  stop ??= stall.reason();
};

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  // Asked every cycle rather than once at the start, so a remount or a broken tool costs a single
  // cycle instead of the rest of the run.
  if (!dismount()) {
    stop = 'could not get off the mount';
    break;
  }

  if (!equipPickaxe()) {
    stop = 'no pickaxe';
    break;
  }

  // The backstop rather than the plan - a spot running dry normally sends the ore to the beetle long
  // before the pack fills. Ore weighs twelve stones and an ingot almost nothing, and there is
  // nowhere else for the weight to go, which is why a smelt that frees nothing ends the run.
  if (tooHeavy()) {
    const oreBefore = oreTotal();

    // Unconditional, because the decision has already been taken: a helper that asked tooHeavy() a
    // second time could disagree, and the run stopped for weight without ever having tried.
    groupOres();
    smeltAll();

    // Ore leaving the pack is the proof a smelt landed, not the weight going down: the client can
    // still be reporting the figure it had before a conversion the pack diff has confirmed, and
    // reading that as 'smelting freed nothing' ended runs next to a working beetle.
    if (oreTotal() < oreBefore) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    // Likeliest reason is a hue given up on earlier - a beetle briefly out of range looks exactly
    // like an ore that cannot be worked. Returns false once there is nothing left to reconsider, so
    // this cannot become a loop.
    if (retryUnsmeltable()) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    stop =
      `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, ` +
      'and smelting freed nothing';
    break;
  }

  const { vein, respawnsAt } = scanForVein();

  if (!vein) {
    if (respawnsAt === undefined) {
      // The likeliest way a run ends on a shard whose tile numbering ORE_TILE_GRAPHICS does not
      // match, and 'no ore in range' says nothing you can act on - so name what the scan rejected.
      log('mining: nothing matched, here is what is actually on the ground');
      reportTerrain(SCAN_RADIUS, SURVEY_ARTS);

      stop = 'no ore in range';
      break;
    }

    idleUntil(respawnsAt);
    continue;
  }

  if (vein.distance > MINE_RANGE) {
    // Coarser than the block map's key on purpose: a tile carries several arts, and once one is
    // written off the next is the same walk. Two *different* veins taking turns as nearest still
    // reset it - the stall watchdog in endCycle is what bounds that.
    const key = `${vein.x},${vein.y}`;
    if (key !== walkingTo) {
      walkingTo = key;
      steps = 0;
    }

    // Blocked or out of patience: set the tile aside, or the next scan picks the same vein again
    if (!stepToward(vein) || ++steps > MAX_STEPS) {
      markUnreachable(vein);
      walkingTo = undefined;
    }

    endCycle('walking', cycle);
    continue;
  }

  walkingTo = undefined;

  // digOnce takes this same snapshot for its own silent-outcome read. Left duplicated: it is one
  // pack walk, against widening what every test reads out of a swing.
  const oreBefore = oreTotal();

  const outcome = digOnce(pickaxeSerial());

  switch (outcome) {
    case 'dug':
      mined++;
      unknown = 0;
      throttled = 0;
      barren = 0;
      stall.progressed();

      // Ore arrives as a new pile rather than joining the one already there. Grouping every swing
      // keeps the pack at one pile per hue, so the item cap is never approached by pile count alone
      // - packFull destroys the ore of the swing that hits it - and nothing sits below
      // MIN_SMELT_AMOUNT when the smelt comes.
      waitForOre(oreBefore);
      groupOres();
      break;

    // Worked out, not dead: markDepleted times it out and the scan picks it up again in
    // RESPAWN_DELAY.
    case 'empty':
      markDepleted(vein);
      unknown = 0;
      groupAndSmelt();
      break;

    // The shard answering about where you stand rather than about a tile. Everything in reach goes
    // on the respawn cooldown together so the loop walks off; parking only the vein it happened to
    // pick left the character swinging at the spot the shard had just written off, which is how a
    // run ended before this had a bucket of its own.
    case 'nothingNearby':
      markAreaDepleted(MINE_RANGE);
      unknown = 0;

      // Said once, at the point it stops looking like bad luck: a run that walks from empty spot to
      // empty spot is what a wrong ORE_TILE_GRAPHICS looks like from the outside.
      if (++barren === NOTHING_NEARBY_HINT) {
        log(
          `mining: ${NOTHING_NEARBY_HINT} spots in a row had nothing to harvest - ` +
            'ORE_TILE_GRAPHICS is probably matching ground that carries no ore',
        );
        reportTerrain(MINE_RANGE, SURVEY_ARTS);
      }

      groupAndSmelt();
      break;

    // A wrong band in ORE_TILE_GRAPHICS is a whole stretch of mountain, so ban the graphic rather
    // than walking to its copies one at a time
    case 'notOre':
      markNotMineable(vein);
      markUnusable(vein, 'cannot be mined');
      unknown = 0;
      break;

    // Already inside MINE_RANGE, so the shard disagrees about the range rather than the walk having
    // fallen short
    case 'tooFar':
      markUnusable(vein, `is out of reach at ${vein.distance} tiles`);
      unknown = 0;
      break;

    // Line of sight: walking closer would not help and neither would waiting
    case 'notSeen':
      markUnusable(vein, 'is not in line of sight');
      unknown = 0;
      break;

    // The ore this swing produced was destroyed rather than dropped, so swinging again destroys
    // more. A full pack is a container at its item cap, so consolidating is the fix: forty piles of
    // one become one pile of forty. If weight is the real problem, the next cycle smelts.
    case 'packFull':
      log('mining: pack is full, consolidating before the next swing');
      groupOres();
      unknown = 0;
      break;

    case 'wornOut':
      log('mining: pickaxe worn out, swapping');
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
      log(`mining: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // With a pickaxe demonstrably in hand this is the shard declining to start the swing, which on a
    // live run was a third of them. digOnce has already looked for a reason, so this is a refusal
    // with nothing said about it - backed off like one, on a budget of its own.
    case 'noCursor':
      noCursor++;
      log(`mining: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
      sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (noCursor >= MAX_NO_CURSOR) {
        stop = 'the shard never opened a target cursor';
      }
      break;

    default:
      unknown++;
      log(`mining: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
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

  if (mined >= reported + LOG_EVERY) {
    reported = mined;
    log(`mining: ${mined} swings, ${oreTotal()} ore, ${player.weight}/${player.weightMax}`);
  }

  endCycle(outcome ?? 'unknown', cycle);
  sleep(STEP_DELAY);
}

// Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth, and
// a run that ended on a stop reason has usually ended because something is wrong.
groupOres();
if (tooHeavy()) {
  smeltAll();
}

// Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
log(`mining: ${mined} swings, ${oreTotal()} ore still in the pack`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business
log(`mining: stopping - ${reason}`);
exit(`mining: ${reason}`);
