// Mines the spot you are standing on until the shard says there is nothing left in it, and then
// stops. The stationary half of dist/mining.js: no scan, no walk, no block map and no respawn wait.
//
// It can leave all of that out because of how the swing works here - dig.ts answers the target
// cursor with yourself and lets the shard pick the ore, so a swing is aimed by where the character
// stands rather than by naming a tile. Everything in vein.ts exists to decide where that is. Stand
// somewhere worth standing and none of it has anything left to do.
//
// The one promise this script makes beyond that is that it does not move at all, which is why the
// smelt is smeltHere rather than smeltAll: a beetle that has wandered off is a pass skipped, not a
// walk taken.
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { overweight } from '../lib/weight.js';
import {
  LOG_EVERY,
  MAX_CYCLES,
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

// Learn the pickaxe graphic from the one you start the script holding
rememberPickaxe(player.equippedItems.oneHanded);

const tooHeavy = (): boolean => overweight();

// The ending this script is written for, named because the summary at the bottom has to tell it
// apart from the several endings that mean something went wrong
const WORKED_OUT = 'the spot is worked out';

log(`mine-here: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);

// The world as the script sees it before it touches anything, the same line dist/mining.js opens
// with and for the same reason: a run that stops on its first cycle otherwise looks exactly like a
// script that never started. The position matters more here than it does there - where the
// character is standing is the whole premise, and it is the one thing this script will not change.
const startingHand = player.equippedItems.oneHanded;
log(
  `mine-here: mounted ${player.equippedItems.mount ? 'yes' : 'no'}, ` +
    `hand ${startingHand ? `0x${startingHand.graphic.toString(16)} '${startingHand.name ?? ''}'` : 'empty'}, ` +
    `weight ${player.weight}/${player.weightMax}`,
);

let mined = 0;
let unknown = 0;
let stop: string | undefined;

// The tally at the last progress line, compared against rather than `mined % LOG_EVERY`: that is a
// property of the count and not of the cycle, so it stays true for every cycle after the twenty-
// fifth swing and a run that then waits or is refused reprints the same line each time.
let reported = 0;

// Consecutive refusals to swing
let throttled = 0;

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

  // Both asked every cycle rather than once at the start: a remount or a broken tool then costs a
  // single cycle instead of the rest of the run, and both are one layer read in the common case.
  if (!dismount()) {
    stop = 'could not get off the mount';
    break;
  }

  if (!equipPickaxe()) {
    stop = 'no pickaxe';
    break;
  }

  // Weight is a real ending here in a way it is not in dist/mining.js. That run works a spot out,
  // smelts, and walks to the next one, so the pack empties long before it fills; this one only ever
  // has the spot it is standing on, and a beetle out of range is a beetle it will not walk to. So
  // the backstop is the same shape - smelt, prove it landed, reconsider the write-offs, then give up
  // - and the ending it leads to is worth reading as "put the beetle next to me" rather than a bug.
  if (tooHeavy()) {
    const oreBefore = oreTotal();

    // Smelted unconditionally: the decision was taken by the branch, and asking a second time inside
    // a helper is how a live run once stopped overweight without ever having tried.
    groupOres();
    smeltHere();

    // Ore leaving the pack is the proof that a smelt landed, not the weight going down - the
    // client's own weight can still be reporting its pre-smelt figure when the pack diff has already
    // confirmed the conversion.
    if (oreTotal() < oreBefore) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    // Nothing moved, and the likeliest reason is a hue given up on earlier - a beetle that stepped
    // out of range for a few passes is indistinguishable from an ore that cannot be worked. Returns
    // false once there is nothing left to reconsider, so this cannot become a loop.
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

  // digOnce takes this same snapshot for its own silent-outcome read. Left duplicated rather than
  // threaded out of it: it is one pack walk, and it is what waitForOre below is measured against.
  const oreBefore = oreTotal();

  const outcome = digOnce(pickaxeSerial());

  switch (outcome) {
    case 'dug':
      mined++;
      unknown = 0;
      throttled = 0;
      stall.progressed();

      // Ore arrives as a new pile rather than joining the one already there, so this keeps the pack
      // at one pile per hue: the item cap - which is what packFull is, and packFull destroys the ore
      // of the swing that hits it - is then never approached by pile count alone, and no ore is left
      // sitting below MIN_SMELT_AMOUNT when the smelt comes.
      waitForOre(oreBefore);
      groupOres();
      break;

    // The two ways the shard says there is nothing left, and this script does not distinguish them.
    // In dist/mining.js they differ by scope - one parks a tile, the other parks everything within
    // reach - and the scope is what decides where to walk next. There is no next here and no tile
    // being booked, so both mean the same thing: the spot is worked out and the run is over.
    //
    // Smelted first, and this is the moment the whole run has been carrying ore towards: the swings
    // are finished, the character is standing exactly where it started, and the beetle that has been
    // following it is either in range now or was never going to be.
    case 'empty':
    case 'nothingNearby':
      groupOres();
      smeltHere();
      stop = WORKED_OUT;
      break;

    // "You can't mine that" about a swing that named no tile is the shard saying this spot is not
    // mineable at all. dist/mining.js bans the art and walks to a different one; there is nothing to
    // ban here and nowhere to walk, so it is an ending.
    case 'notOre':
      stop = 'nothing here can be mined';
      break;

    // Range and line of sight, for a swing aimed at where the character is standing. Neither can be
    // answered by moving, because moving is the one thing this script does not do - so they are
    // ended rather than retried, and named separately because they mean different things about the
    // spot: one is a shard that wanted a tile after all, the other is something in the way.
    case 'tooFar':
      stop = 'the shard says the ore is out of reach from where you are standing';
      break;

    case 'notSeen':
      stop = 'the shard cannot see the ore from where you are standing';
      break;

    // The ore this swing produced was destroyed rather than dropped, so swinging again would only
    // destroy more. Consolidating is the answer rather than smelting, because a full pack is a
    // container at its item cap: forty piles of one become one pile of forty, and thirty-nine slots
    // come back. If weight is the real problem, the next cycle's tooHeavy() branch smelts.
    case 'packFull':
      log('mine-here: pack is full, consolidating before the next swing');
      groupOres();
      unknown = 0;
      break;

    case 'wornOut':
      log('mine-here: pickaxe worn out, swapping');
      unknown = 0;
      break;

    // Nothing was learned and nothing went wrong: the shard was busy writing its world file. The
    // counters are reset rather than merely left alone, because whatever they had accumulated was
    // measured against a server that was not answering - and the stall watchdog with them, since a
    // shard that saves often would otherwise walk a run to STALL_STOP a save at a time.
    case 'saving':
      waitOutSave();
      unknown = 0;
      throttled = 0;
      stall.progressed();
      break;

    // A fixed retry shorter than the harvest delay re-arms the very timer it is waiting on, so back
    // off further each time instead, and give up rather than spin
    case 'throttled':
      throttled++;

      // A refusal is a read outcome, so it clears the unreadable count the way every other named
      // branch does. Left standing, a shard alternating refusals with silence would end the run on
      // MAX_UNKNOWN without ever having produced five unreadable cycles in a row.
      unknown = 0;
      log(`mine-here: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // A cursor that never opened, with a pickaxe demonstrably in hand, is the shard declining to
    // start the swing rather than an empty hand. Backed off like a throttle, but still counted.
    case 'noCursor':
      unknown++;
      sleep(THROTTLE_BACKOFF);
      break;

    default:
      unknown++;
      log(`mine-here: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
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

// Tidied on the way out, and smelted only if the run is ending over the limit. The worked-out
// ending has already smelted by the time it gets here, and every other ending is something being
// wrong - what is in the pack then is ore that keeps perfectly well as ore.
groupOres();
if (tooHeavy()) {
  smeltHere();
}

// A run that stops for a worked-out spot without ever having landed a swing did not work anything
// out: it was standing somewhere with no ore in it. Said plainly, because the stop reason on its own
// reads like the end of a good run rather than the start of a bad one. Not said for the other
// endings - a broken tool or a shard refusing to answer says nothing about where you are standing.
if (stop === WORKED_OUT && mined === 0) {
  log('mine-here: no swing ever landed - the character is probably not standing next to a vein');
}

// Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
log(`mine-here: ${mined} swings, ${oreTotal()} ore still in the pack`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`mine-here: stopping - ${reason}`);
exit(`mine-here: ${reason}`);
