import { backoffFor, createIdleWait, createStallWatch } from '../lib/loop.js';
import { overweight } from '../lib/weight.js';
import {
  IDLE_LOG_EVERY,
  IDLE_POLL,
  LOG_EVERY,
  MAX_CYCLES,
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

// Learn the pickaxe graphic from the one you start the script holding
rememberPickaxe(player.equippedItems.oneHanded);

const idleUntil = createIdleWait({
  prefix: 'mining',
  waitingFor: 'everything in reach is worked out',
  pollMs: IDLE_POLL,
  logEveryMs: IDLE_LOG_EVERY,
  stopReason,
  onDone: resetBeat,
});

// Smelting happens for one reason only: the pack is over the limit and the shard has started
// refusing to move things. Not on a depleted vein, not at a buffer below the limit, not at the end
// of the run - ore travels as ore until it cannot travel at all. No buffer, for the same reason.
const tooHeavy = (): boolean => overweight();

// What a spot running dry is for. The swings that filled the pack are over, the character is about
// to walk somewhere else regardless, and the beetle is a pet that has been following it the whole
// time - so this is the cheapest moment in the run to turn a pack of ore into a pocketful of ingots,
// and it comes round long before the weight does.
//
// This used to be left to the weight alone, on the reasoning that a depleted vein says nothing about
// how heavy the pack is and that walking to the beetle every time one runs dry is a lot of walking.
// Both are still true. What makes the trade worth taking is that neither call costs anything when
// there is nothing to do: groupOres is a single scan of a pack that is already grouped, and smeltAll
// asks whether any pile is worth smelting before it so much as looks for the beetle.
const groupAndSmelt = (): void => {
  groupOres();
  smeltAll();
};

log(`mining: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);

// The world as the script sees it before it touches anything. A run that stops on its first cycle
// is the hardest kind to diagnose from the outside - it looks like a script that did not start at
// all - so the three things that end one that early get said out loud first.
const startingHand = player.equippedItems.oneHanded;
log(
  `mining: mounted ${player.equippedItems.mount ? 'yes' : 'no'}, ` +
    `hand ${startingHand ? `0x${startingHand.graphic.toString(16)} '${startingHand.name ?? ''}'` : 'empty'}, ` +
    `weight ${player.weight}/${player.weightMax}`,
);

let mined = 0;
let unknown = 0;
let stop: string | undefined;

// The tally at the last progress line. Compared against rather than `mined % LOG_EVERY`, which is a
// property of the count and not of the cycle: it stays true for every cycle that follows the
// twenty-fifth swing, so a run that then walks, waits or is refused reprints the same line each time.
let reported = 0;

// Consecutive refusals to swing
let throttled = 0;

// Spots in a row the shard said had nothing in them. A few is roaming; a lot in a row is the seeded
// ORE_TILE_GRAPHICS matching ground that carries no ore, which looks identical from the outside.
let barren = 0;

// Steps spent on the vein we are currently walking to, reset when the target changes
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

  // The backstop rather than the plan. A spot running dry is what normally sends the ore to the
  // beetle, and that happens long before the pack fills - but nothing says a run has to work a spot
  // out before it caps, and there is no weight guard in stopReason to catch one that does. So this
  // stays: ore weighs twelve stones and an ingot almost nothing, and there is nowhere else for the
  // weight to go, which is why a smelt that frees nothing here ends the run rather than slowing it.
  if (tooHeavy()) {
    const oreBefore = oreTotal();

    // Smelted unconditionally, because the decision has already been taken. This used to go through
    // a helper that asked tooHeavy() a second time, and the two answers could differ: the branch
    // opened, the helper declined to smelt, and the run stopped for being overweight without ever
    // having tried. A condition is checked where it is decided, not again where it is acted on.
    groupOres();
    smeltAll();

    // Ore leaving the pack is the proof that a smelt landed, not the weight going down. The
    // client's own weight can still be reporting the figure it had before a conversion the pack
    // diff has already confirmed, and reading that as 'smelting freed nothing' ended runs standing
    // next to a working beetle with a pack full of perfectly good ore.
    if (oreTotal() < oreBefore) {
      endCycle('smelting', cycle);
      sleep(STEP_DELAY);
      continue;
    }

    // Nothing moved, and the likeliest reason is a hue given up on earlier - a beetle that stepped
    // out of range for a few passes is indistinguishable from an ore that cannot be worked. Clear
    // those verdicts and let the next cycle try them properly before ending the run over weight the
    // pack is still full of. Returns false once there is nothing left to reconsider, so this cannot
    // become a loop.
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

  // Nothing to mine now, but something is coming back: wait for it rather than ending a run that
  // only has to sit still to have a mountain again
  if (!vein) {
    if (respawnsAt === undefined) {
      // Standing on a mountain and being told 'no ore in range' says nothing you can act on, and
      // this is the likeliest way the run ends on a shard whose tile numbering the seeded
      // ORE_TILE_GRAPHICS does not match. So name what the scan did see and rejected: the arts
      // under your feet are the candidates to add.
      log('mining: nothing matched, here is what is actually on the ground');
      reportTerrain(SCAN_RADIUS, SURVEY_ARTS);

      stop = 'no ore in range';
      break;
    }

    idleUntil(respawnsAt);
    continue;
  }

  if (vein.distance > MINE_RANGE) {
    // Coarser than the block map's key on purpose: a tile carries several arts, and once one of
    // them is written off the next is the same walk, so the step count should carry over rather
    // than start again. Two *different* veins taking turns as nearest still resets this, and no
    // per-target counter can catch that - the stall watchdog in endCycle is what bounds it.
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

  // digOnce takes this same snapshot for its own silent-outcome read. Left duplicated rather than
  // threaded out of it: it is one pack walk, and widening what a swing returns to carry a number the
  // caller can ask for itself is not worth the change to every test that reads an outcome.
  const oreBefore = oreTotal();

  const outcome = digOnce(pickaxeSerial());

  switch (outcome) {
    case 'dug':
      mined++;
      unknown = 0;
      throttled = 0;
      barren = 0;
      stall.progressed();

      // Ore arrives as a new pile rather than joining the one already there, so grouping only when
      // something complains lets a swing's worth of piles accumulate between complaints. Doing it
      // here keeps the pack at one pile per hue at all times: the item cap - which is what packFull
      // is, and packFull destroys the ore of the swing that hits it - is then never approached by
      // pile count alone, and no ore is left sitting below MIN_SMELT_AMOUNT when the smelt comes.
      waitForOre(oreBefore);
      groupOres();
      break;

    // The vein is worked out, not dead: markDepleted times it out and the scan picks it up again
    // in RESPAWN_DELAY. This is also the moment the ore it gave goes to the beetle - see
    // groupAndSmelt.
    case 'empty':
      markDepleted(vein);
      unknown = 0;
      groupAndSmelt();
      break;

    // The shard answering about where you stand rather than about a tile, which is what a swing
    // that names no tile mostly gets. Everything in reach goes on the respawn cooldown together,
    // so the next scan has to look further out and the loop walks off. Parking only the vein it
    // happened to pick would leave the character standing on the spot the shard just wrote off,
    // swinging for the same sentence until the run ended - which is exactly how it did end before
    // this had a bucket of its own.
    case 'nothingNearby':
      markAreaDepleted(MINE_RANGE);
      unknown = 0;

      // Said once, at the point it stops looking like bad luck. A run that walks from empty spot to
      // empty spot all afternoon is what a wrong ORE_TILE_GRAPHICS looks like from the outside -
      // the scan keeps finding 'ore' because the table says so, and the shard keeps disagreeing.
      // The arts listed are the ones right under the character, so they are the ones to correct.
      if (++barren === NOTHING_NEARBY_HINT) {
        log(
          `mining: ${NOTHING_NEARBY_HINT} spots in a row had nothing to harvest - ` +
            'ORE_TILE_GRAPHICS is probably matching ground that carries no ore',
        );
        reportTerrain(MINE_RANGE, SURVEY_ARTS);
      }

      // The same event as `empty` at a wider scope - the swing aims by where the character stands
      // rather than by naming a tile, so this is the shard writing off everything in reach instead
      // of one square. It is about to walk off a worked-out spot either way, so it smelts either way.
      groupAndSmelt();
      break;

    // The whole art is scenery, not just this tile - a wrong band in ORE_TILE_GRAPHICS is a whole
    // stretch of mountain - so ban the graphic and stop walking to its copies one at a time
    case 'notOre':
      markNotMineable(vein);
      markUnusable(vein, 'cannot be mined');
      unknown = 0;
      break;

    // Already inside MINE_RANGE, so this is the shard disagreeing about the range rather than a
    // walk that fell short. Treat the tile as unreachable instead of swinging at it again.
    case 'tooFar':
      markUnusable(vein, `is out of reach at ${vein.distance} tiles`);
      unknown = 0;
      break;

    // Line of sight, so walking closer would not help and neither would waiting - something is
    // simply in the way
    case 'notSeen':
      markUnusable(vein, 'is not in line of sight');
      unknown = 0;
      break;

    // The ore this swing produced was destroyed rather than dropped, so swinging again would only
    // destroy more. The vein is untouched - it is the pack that has to give. Consolidating is the
    // answer rather than smelting, because a full pack is a container at its item cap: forty piles
    // of one become one pile of forty, and thirty-nine slots come back. If the weight is the real
    // problem, the next cycle's tooHeavy() branch smelts; if it is not, this is the cheaper fix.
    case 'packFull':
      log('mining: pack is full, consolidating before the next swing');
      groupOres();
      unknown = 0;
      break;

    case 'wornOut':
      log('mining: pickaxe worn out, swapping');
      unknown = 0;
      break;

    // Nothing was learned about the vein and nothing went wrong: the shard was busy. The counters
    // are reset rather than merely left alone, because whatever they had accumulated was measured
    // against a server that was not answering.
    // Sitting out a save is the script working, not the script stuck, so the stall watchdog is
    // reset along with the rest: a shard that saves often would otherwise walk a run to STALL_STOP
    // a save at a time, and the respawn wait is already excused on exactly this reasoning.
    case 'saving':
      waitOutSave();
      unknown = 0;
      throttled = 0;
      stall.progressed();
      break;

    // A fixed retry shorter than the harvest delay re-arms the very timer it is waiting on, so
    // back off further each time instead, and give up rather than spin
    case 'throttled':
      throttled++;

      // A refusal is a read outcome, so it clears the unreadable count the way every other named
      // branch does. Left standing, a shard alternating refusals with silence ends the run on
      // MAX_UNKNOWN without ever having produced five unreadable cycles in a row.
      unknown = 0;
      log(`mining: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the swing';
      }
      break;

    // A cursor that never opened, with a pickaxe demonstrably in hand, is the shard declining to
    // start the swing rather than an empty hand - which on a live run turned out to be a third of
    // them. Backed off like a throttle, but still counted: five in a row with nothing else
    // happening is a stuck run whatever the cause.
    case 'noCursor':
      unknown++;
      sleep(THROTTLE_BACKOFF);
      break;

    default:
      unknown++;
      log(`mining: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
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

// Tidied on the way out, and smelted only if the run is ending over the limit. Left alone
// deliberately: what is in the pack here is the ore mined since the last spot ran dry, which is a
// few swings' worth rather than a haul, and a run that ends on a stop reason has usually ended
// because something is wrong - walking off to a beetle is not what to do about that.
groupOres();
if (tooHeavy()) {
  smeltAll();
}

// Swings rather than an ore delta: smelted ore has left the pack, so the pack cannot total the run
const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
log(`mining: ${mined} swings, ${oreTotal()} ore still in the pack`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`mining: stopping - ${reason}`);
exit(`mining: ${reason}`);
