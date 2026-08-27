import { die } from '../lib/die.js';
import { hex } from '../lib/entity.js';
import { runHarvest, type Approach, type Handled, type Interlude } from '../lib/harvest.js';
import { createStallWatch } from '../lib/loop.js';
import { carveOnce } from './carve.js';
import {
  BLOCKED_DELAY,
  CARVE_RANGE,
  LOG_EVERY,
  LOOT_CORPSES,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  PRUNE_EVERY,
  STALL_STOP,
  STALL_WARN,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  WATCH_POLL,
} from './config.js';
import { describeGround, inReach, nearest, nextToCarve, onGround, prune } from './corpses.js';
import { stopReason } from './guards.js';
import { heartbeat } from './heartbeat.js';
import { knifeSerial } from './knife.js';
import { pending, take } from './loot.js';
import { memory, now } from './memory.js';
import { isSaving, waitOutSave } from './save.js';

const packSerial = player.backpack?.serial ?? die('carve: no backpack to put the feathers in');

// A wrong graphic is otherwise an afternoon of silence, so the count is the first thing said
log(`carve: watching within ${CARVE_RANGE} tiles - ${describeGround()} in the world`);

let carved = 0;
let taken = 0;
let waits = 0;
let saidOutOfReach = false;

const setAside = (corpse: Item, why: string): Handled => {
  memory().blocked.set(corpse.serial, now() + BLOCKED_DELAY);
  log(`carve: ${hex(corpse.serial)} ${why}, leaving it for ${BLOCKED_DELAY / 1000}s`);

  return {};
};

const handle = (outcome: string, corpse?: Item): Handled => {
  if (!corpse) {
    return undefined;
  }

  const { done, emptied } = memory();

  switch (outcome) {
    // Nothing left to carve is not nothing left to take: a corpse someone else carved, or one this
    // run carved before its memory was lost, can still be holding the feathers.
    case 'nothingLeft':
      done.add(corpse.serial);

      return {};

    case 'notCarvable':
      done.add(corpse.serial);
      emptied.add(corpse.serial);

      return {};

    // Already inside CARVE_RANGE, so the shard disagrees about the range rather than the script
    // having misjudged it
    case 'tooFar':
      return setAside(corpse, 'is out of reach');

    case 'notSeen':
      return setAside(corpse, 'is not in line of sight');

    default:
      return undefined;
  }
};

runHarvest<Item>({
  prefix: 'carve',
  landed: 'carved',
  toolName: 'butcher knife',

  stopReason,
  isSaving,
  waitOutSave,

  equipTool: () => knifeSerial() !== undefined,

  relieve: (): Interlude => {
    if (!LOOT_CORPSES) {
      return undefined;
    }

    const corpse = pending(inReach(onGround(), CARVE_RANGE));

    if (!corpse) {
      return undefined;
    }

    const took = take(corpse, packSerial);

    if (took.items > 0) {
      taken += took.items;
      log(`carve: took ${took.items} from ${hex(corpse.serial)}, ${taken} in total`);
    }

    return { phase: 'looting' };
  },

  approach: (): Approach<Item> => {
    const all = onGround();
    const corpse = nextToCarve(inReach(all, CARVE_RANGE));

    if (corpse) {
      saidOutOfReach = false;

      return { target: corpse };
    }

    const closest = nearest(all);

    // Said once: a field of corpses that are all out of reach logs identically to an empty one, and
    // it is what a wrong CARVE_RANGE looks like from the outside
    if (closest !== undefined && !saidOutOfReach) {
      saidOutOfReach = true;
      log(
        `carve: ${all.length} corpses about, nearest ${closest} tiles away - ` +
          `nothing within ${CARVE_RANGE} left to carve`,
      );
    }

    // Only on the idle path, and only every so often: this is a findObject per remembered serial,
    // and the sets only grow while the script has nothing else to do anyway.
    if (++waits % PRUNE_EVERY === 0) {
      prune();
    }

    // Beaten here rather than by the runner: waiting deliberately skips endCycle, and a script
    // standing in a quiet field is otherwise indistinguishable from a hung one.
    heartbeat.beat('watching', waits, carved);
    sleep(WATCH_POLL);

    return { waited: true };
  },

  harvest: (corpse) => {
    const knife = knifeSerial();

    if (!corpse || knife === undefined) {
      return undefined;
    }

    const outcome = carveOnce(corpse, knife);

    if (outcome === 'carved') {
      carved++;
      memory().done.add(corpse.serial);
    }

    return outcome;
  },

  handle,

  progress: (tally) => `${tally} carved, ${taken} taken`,

  finish: (tally) => log(`carve: ${tally} corpses carved, ${taken} items taken`),

  stall: createStallWatch({
    prefix: 'carve',
    without: 'cycles without a carve landing',
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
