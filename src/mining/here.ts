// The stationary half of dist/mining.js: no scan, no walk, no block map and no respawn wait. It can
// leave all of that out because dig.ts answers the cursor with yourself, so a swing is aimed by
// where the character stands rather than by naming a tile.
//
// It does not move at all, which is why the smelt is smeltHere rather than smeltAll: a beetle that
// has wandered off is a pass skipped, not a walk taken.
import { describeItem } from '../lib/entity.js';
import { runHarvest, type Handled, type Interlude } from '../lib/harvest.js';
import { createStallWatch } from '../lib/loop.js';
import { overweight } from '../lib/weight.js';
import {
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  PICK_BEETLE,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { digOnce } from './dig.js';
import { stopReason } from './guards.js';
import { heartbeat } from './heartbeat.js';
import { dismount } from './mount.js';
import { groupOres, oreTotal, waitForOre } from './ore.js';
import { equipPickaxe, pickaxeSerial, rememberPickaxe } from './pickaxe.js';
import { waitOutSave } from './save.js';
import { pickBeetle, retryUnsmeltable, smeltHere } from './smelt.js';
import { watchForTrouble } from './threat.js';

rememberPickaxe(player.equippedItems.oneHanded);

const tooHeavy = (): boolean => overweight();

const WORKED_OUT = 'the spot is worked out';

log(`mine-here: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);

// A run that stops on its first cycle looks from the outside like one that never started. The
// position matters more here than in dist/mining.js: where the character stands is the whole premise.
// Read before the dismount below, or the mounted half of it always answers no.
log(
  `mine-here: mounted ${player.equippedItems.mount ? 'yes' : 'no'}, ` +
    `hand ${describeItem(player.equippedItems.oneHanded)}, ` +
    `weight ${player.weight}/${player.weightMax}`,
);

// Before the cursor, so the beetle you click is one standing next to you rather than the one you are
// sitting on
const afoot = dismount();

if (PICK_BEETLE) {
  pickBeetle();
}

// A pack that arrives full has no room for the first swing's ore, and the loop would find that out by
// destroying it. Smelting only once off the mount: a smelt aimed at the beetle you ride is silent,
// and three silent passes write the hue off before the run has started.
groupOres();

if (afoot && tooHeavy()) {
  smeltHere();
}

let oreBefore = 0;

// A real ending here in a way it is not in dist/mining.js, which empties the pack every time it walks
// on: a beetle out of range is a beetle this run will not walk to. Read the ending it leads to as
// "put the beetle next to me" rather than as a bug.
const smeltForRoom = (): Interlude => {
  if (!tooHeavy()) {
    return undefined;
  }

  const before = oreTotal();

  // Unconditional: asking tooHeavy() a second time inside a helper is how a live run once stopped
  // overweight without ever having tried.
  groupOres();
  smeltHere();

  // Ore leaving the pack is the proof a smelt landed, not the weight going down: the client can
  // still be reporting its pre-smelt figure when the pack diff has confirmed the conversion.
  if (oreTotal() < before) {
    return { phase: 'smelting' };
  }

  // Likeliest reason is a hue given up on earlier - a beetle briefly out of range looks exactly like
  // an ore that cannot be worked. False once a retry has been spent without freeing any ore, which is
  // what stops this cycling through 'smelting' until the stall watchdog.
  if (retryUnsmeltable()) {
    return { phase: 'smelting' };
  }

  // The last thing tried rather than a second helping of the first: the retry above has just reopened
  // the hues written off, so this pass is the one that can act on them.
  groupOres();
  smeltHere();

  if (oreTotal() < before) {
    return { phase: 'smelting' };
  }

  return {
    stop:
      `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, ` +
      'and smelting freed nothing - the beetle has to be standing next to you',
  };
};

const handle = (outcome: string): Handled => {
  switch (outcome) {
    // The two ways the shard says there is nothing left. In dist/mining.js they differ by scope,
    // which is what decides where to walk next; there is no next here, so both mean the same thing.
    case 'empty':
    case 'nothingNearby':
      groupOres();
      smeltHere();

      return { stop: WORKED_OUT };

    // About a swing that named no tile, so the shard is saying this spot is not mineable at all.
    // Nothing to ban and nowhere to walk, so it is an ending.
    case 'notOre':
      return { stop: 'nothing here can be mined' };

    // Range and line of sight, neither of which can be answered by moving - the one thing this
    // script does not do. Named separately because one is a shard that wanted a tile after all and
    // the other is something in the way.
    case 'tooFar':
      return { stop: 'the shard says the ore is out of reach from where you are standing' };

    case 'notSeen':
      return { stop: 'the shard cannot see the ore from where you are standing' };

    // The ore this swing produced was destroyed rather than dropped, so swinging again destroys
    // more. A full pack is a container at its item cap, so consolidating is the fix: forty piles of
    // one become one pile of forty. If weight is the real problem, the next cycle smelts.
    case 'packFull':
      log('mine-here: pack is full, consolidating before the next swing');
      groupOres();

      return {};

    default:
      return undefined;
  }
};

runHarvest({
  prefix: 'mine-here',
  landed: 'dug',
  toolName: 'pickaxe',

  stopReason,
  watch: watchForTrouble('mine-here'),
  equipTool: equipPickaxe,
  ready: () => (dismount() ? undefined : 'could not get off the mount'),
  relieve: smeltForRoom,
  waitOutSave,

  harvest: () => {
    oreBefore = oreTotal();

    return digOnce(pickaxeSerial());
  },

  // Ore arrives as a new pile rather than joining the one already there. Grouping every swing keeps
  // the pack at one pile per hue, so the item cap is never approached by pile count alone - packFull
  // destroys the ore of the swing that hits it.
  onLanded: () => {
    waitForOre(oreBefore);
    groupOres();
  },

  handle,

  progress: (mined) => `${mined} swings, ${oreTotal()} ore`,

  finish: (mined, reason) => {
    // The worked-out ending has already smelted by the time it gets here, and every other ending is
    // something being wrong - what is in the pack then keeps perfectly well as ore.
    groupOres();

    if (tooHeavy()) {
      smeltHere();
    }

    // A worked-out ending with no swing landed did not work anything out: it was standing somewhere
    // with no ore in it, and the stop reason alone reads like the end of a good run.
    if (reason === WORKED_OUT && mined === 0) {
      log(
        'mine-here: no swing ever landed - the character is probably not standing next to a vein',
      );
    }

    // Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the
    // run
    log(`mine-here: ${mined} swings, ${oreTotal()} ore still in the pack`);
  },

  stall: createStallWatch({
    prefix: 'mine-here',
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
