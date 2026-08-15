// The stationary half of dist/mining.js: no scan, no walk, no block map and no respawn wait. It can
// leave all of that out because dig.ts answers the cursor with yourself, so a swing is aimed by
// where the character stands rather than by naming a tile.
//
// It does not move at all, which is why the smelt is smeltHere rather than smeltAll: a beetle that
// has wandered off is a pass skipped, not a walk taken.
import { describeItem } from '../lib/entity.js';
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { overweight } from '../lib/weight.js';
import {
  LOG_EVERY,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_THROTTLED,
  MAX_UNKNOWN,
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
import { retryUnsmeltable, smeltHere } from './smelt.js';

rememberPickaxe(player.equippedItems.oneHanded);

const tooHeavy = (): boolean => overweight();

const WORKED_OUT = 'the spot is worked out';

log(`mine-here: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);

// A run that stops on its first cycle looks from the outside like one that never started. The
// position matters more here than in dist/mining.js: where the character stands is the whole premise.
log(
  `mine-here: mounted ${player.equippedItems.mount ? 'yes' : 'no'}, ` +
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

const stall = createStallWatch({
  prefix: 'mine-here',
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

  // A real ending here in a way it is not in dist/mining.js, which empties the pack every time it
  // walks on: a beetle out of range is a beetle this run will not walk to. Read the ending it leads
  // to as "put the beetle next to me" rather than as a bug.
  if (tooHeavy()) {
    const oreBefore = oreTotal();

    // Unconditional: asking tooHeavy() a second time inside a helper is how a live run once stopped
    // overweight without ever having tried.
    groupOres();
    smeltHere();

    // Ore leaving the pack is the proof a smelt landed, not the weight going down: the client can
    // still be reporting its pre-smelt figure when the pack diff has confirmed the conversion.
    if (oreTotal() < oreBefore) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    // Likeliest reason is a hue given up on earlier - a beetle briefly out of range looks exactly
    // like an ore that cannot be worked. Returns false once there is nothing left to reconsider.
    if (retryUnsmeltable()) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    stop =
      `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, ` +
      'and smelting freed nothing - the beetle has to be standing next to you';
    break;
  }

  // digOnce takes this same snapshot for its own silent-outcome read; it is one pack walk.
  const oreBefore = oreTotal();

  const outcome = digOnce(pickaxeSerial());

  switch (outcome) {
    case 'dug':
      mined++;
      unknown = 0;
      throttled = 0;
      stall.progressed();

      // Ore arrives as a new pile rather than joining the one already there. Grouping every swing
      // keeps the pack at one pile per hue, so the item cap is never approached by pile count alone
      // - packFull destroys the ore of the swing that hits it.
      waitForOre(oreBefore);
      groupOres();
      break;

    // The two ways the shard says there is nothing left. In dist/mining.js they differ by scope,
    // which is what decides where to walk next; there is no next here, so both mean the same thing.
    case 'empty':
    case 'nothingNearby':
      groupOres();
      smeltHere();
      stop = WORKED_OUT;
      break;

    // About a swing that named no tile, so the shard is saying this spot is not mineable at all.
    // Nothing to ban and nowhere to walk, so it is an ending.
    case 'notOre':
      stop = 'nothing here can be mined';
      break;

    // Range and line of sight, neither of which can be answered by moving - the one thing this
    // script does not do. Named separately because one is a shard that wanted a tile after all and
    // the other is something in the way.
    case 'tooFar':
      stop = 'the shard says the ore is out of reach from where you are standing';
      break;

    case 'notSeen':
      stop = 'the shard cannot see the ore from where you are standing';
      break;

    // The ore this swing produced was destroyed rather than dropped, so swinging again destroys
    // more. A full pack is a container at its item cap, so consolidating is the fix: forty piles of
    // one become one pile of forty. If weight is the real problem, the next cycle smelts.
    case 'packFull':
      log('mine-here: pack is full, consolidating before the next swing');
      groupOres();
      unknown = 0;
      break;

    case 'wornOut':
      log('mine-here: pickaxe worn out, swapping');
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
      log(`mine-here: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // With a pickaxe demonstrably in hand this is the shard declining to start the swing. digOnce
    // has already looked for a reason, so this is a refusal with nothing said about it.
    case 'noCursor':
      noCursor++;
      log(`mine-here: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
      sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (noCursor >= MAX_NO_CURSOR) {
        stop = 'the shard never opened a target cursor';
      }
      break;

    default:
      unknown++;
      log(`mine-here: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
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
    log(`mine-here: ${mined} swings, ${oreTotal()} ore, ${player.weight}/${player.weightMax}`);
  }

  endCycle(outcome ?? 'unknown', cycle);
  sleep(STEP_DELAY);
}

// The worked-out ending has already smelted by the time it gets here, and every other ending is
// something being wrong - what is in the pack then keeps perfectly well as ore.
groupOres();
if (tooHeavy()) {
  smeltHere();
}

// A worked-out ending with no swing landed did not work anything out: it was standing somewhere
// with no ore in it, and the stop reason alone reads like the end of a good run.
if (stop === WORKED_OUT && mined === 0) {
  log('mine-here: no swing ever landed - the character is probably not standing next to a vein');
}

// Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
log(`mine-here: ${mined} swings, ${oreTotal()} ore still in the pack`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business
log(`mine-here: stopping - ${reason}`);
exit(`mine-here: ${reason}`);
