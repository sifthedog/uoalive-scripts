import { describeItem } from '../lib/entity.js';
import { runHarvest, type Handled, type Interlude } from '../lib/harvest.js';
import { createIdleWait, createStallWatch } from '../lib/loop.js';
import { createApproach } from '../lib/tiles.js';
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
  PICK_BEETLE,
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
import { pickBeetle, retryUnsmeltable, smeltAll } from './smelt.js';
import { reportTerrain } from './survey.js';
import { watchForTrouble } from './threat.js';
import {
  markAreaDepleted,
  markDepleted,
  markNotMineable,
  markUnreachable,
  markUnusable,
  scanForVein,
  type Vein,
} from './vein.js';
import { stepToward } from './walk.js';

rememberPickaxe(player.equippedItems.oneHanded);

if (PICK_BEETLE) {
  pickBeetle();
}

const watch = watchForTrouble('mining');

const idleUntil = createIdleWait({
  prefix: 'mining',
  waitingFor: 'everything in reach is worked out',
  pollMs: IDLE_POLL,
  logEveryMs: IDLE_LOG_EVERY,
  stopReason,
  watch,
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

// Spots in a row the shard said had nothing in them. A few is roaming; a lot in a row is
// ORE_TILE_GRAPHICS matching ground that carries no ore, which looks identical from the outside.
let barren = 0;

// Taken inside the swing and read by onLanded, because a swing's ore arrives after the sentence that
// announced it and the pile has to be waited for against the total from before
let oreBefore = 0;

// The backstop rather than the plan - a spot running dry normally sends the ore to the beetle long
// before the pack fills. Ore weighs twelve stones and an ingot almost nothing, and there is nowhere
// else for the weight to go, which is why a smelt that frees nothing ends the run.
const smeltForRoom = (): Interlude => {
  if (!tooHeavy()) {
    return undefined;
  }

  const before = oreTotal();

  // Unconditional, because the decision has already been taken: a helper that asked tooHeavy() a
  // second time could disagree, and the run stopped for weight without ever having tried.
  groupOres();
  smeltAll();

  // Ore leaving the pack is the proof a smelt landed, not the weight going down: the client can
  // still be reporting the figure it had before a conversion the pack diff has confirmed, and
  // reading that as 'smelting freed nothing' ended runs next to a working beetle.
  if (oreTotal() < before) {
    return { phase: 'smelting' };
  }

  // Likeliest reason is a hue given up on earlier - a beetle briefly out of range looks exactly like
  // an ore that cannot be worked. False once a retry has been spent without freeing any ore, which is
  // what stops this cycling through 'smelting' until the stall watchdog.
  if (retryUnsmeltable()) {
    return { phase: 'smelting' };
  }

  return {
    stop:
      `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, ` +
      'and smelting freed nothing',
  };
};

const handle = (outcome: string, vein?: Vein): Handled => {
  if (!vein) {
    return undefined;
  }

  switch (outcome) {
    // Worked out, not dead: markDepleted times it out and the scan picks it up again in
    // RESPAWN_DELAY.
    case 'empty':
      markDepleted(vein);
      groupAndSmelt();

      return {};

    // The shard answering about where you stand rather than about a tile. Everything in reach goes
    // on the respawn cooldown together so the loop walks off; parking only the vein it happened to
    // pick left the character swinging at the spot the shard had just written off, which is how a
    // run ended before this had a bucket of its own.
    case 'nothingNearby':
      markAreaDepleted(MINE_RANGE);

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

      return {};

    // A wrong band in ORE_TILE_GRAPHICS is a whole stretch of mountain, so ban the graphic rather
    // than walking to its copies one at a time
    case 'notOre':
      markNotMineable(vein);
      markUnusable(vein, 'cannot be mined');

      return {};

    // Already inside MINE_RANGE, so the shard disagrees about the range rather than the walk having
    // fallen short
    case 'tooFar':
      markUnusable(vein, `is out of reach at ${vein.distance} tiles`);

      return {};

    // Line of sight: walking closer would not help and neither would waiting
    case 'notSeen':
      markUnusable(vein, 'is not in line of sight');

      return {};

    // The ore this swing produced was destroyed rather than dropped, so swinging again destroys
    // more. A full pack is a container at its item cap, so consolidating is the fix: forty piles of
    // one become one pile of forty. If weight is the real problem, the next cycle smelts.
    case 'packFull':
      log('mining: pack is full, consolidating before the next swing');
      groupOres();

      return {};

    default:
      return undefined;
  }
};

runHarvest<Vein>({
  prefix: 'mining',
  landed: 'dug',
  toolName: 'pickaxe',

  stopReason,
  watch,
  equipTool: equipPickaxe,
  ready: () => (dismount() ? undefined : 'could not get off the mount'),
  relieve: smeltForRoom,
  waitOutSave,

  approach: createApproach<Vein>({
    // Renamed rather than shared: 'vein' and 'respawnsAt' are what this folder's tests read
    scan: () => {
      const { vein, respawnsAt } = scanForVein();

      return { found: vein, readyAt: respawnsAt };
    },

    range: MINE_RANGE,
    maxSteps: MAX_STEPS,
    step: stepToward,
    markUnreachable,
    idleUntil,

    nothingFound: () => {
      // The likeliest way a run ends on a shard whose tile numbering ORE_TILE_GRAPHICS does not
      // match, and 'no ore in range' says nothing you can act on - so name what the scan rejected.
      log('mining: nothing matched, here is what is actually on the ground');
      reportTerrain(SCAN_RADIUS, SURVEY_ARTS);

      return 'no ore in range';
    },
  }),

  harvest: () => {
    oreBefore = oreTotal();

    return digOnce(pickaxeSerial());
  },

  // Ore arrives as a new pile rather than joining the one already there. Grouping every swing keeps
  // the pack at one pile per hue, so the item cap is never approached by pile count alone - packFull
  // destroys the ore of the swing that hits it - and nothing sits below MIN_SMELT_AMOUNT when the
  // smelt comes.
  onLanded: () => {
    barren = 0;
    waitForOre(oreBefore);
    groupOres();
  },

  handle,

  progress: (mined) => `${mined} swings, ${oreTotal()} ore`,

  // Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth,
  // and a run that ended on a stop reason has usually ended because something is wrong.
  finish: (mined) => {
    groupOres();

    if (tooHeavy()) {
      smeltAll();
    }

    // Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the
    // run
    log(`mining: ${mined} swings, ${oreTotal()} ore still in the pack`);
  },

  stall: createStallWatch({
    prefix: 'mining',
    without: 'cycles without a swing landing',
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
