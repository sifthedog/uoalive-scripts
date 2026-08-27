import { die } from '../lib/die.js';
import { backoffFor } from '../lib/loop.js';
import {
  GRAB_RANGE,
  MAX_CYCLES,
  MAX_QUIET_SWEEPS,
  SWEEP_BACKOFF,
  SWEEP_BACKOFF_MAX,
  WATCH_POLL,
} from './config.js';
import { describeFloor, inReach, nearest, onFloor } from './floor.js';
import { settle, sweep } from './grab.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { isSaving, waitOutSave } from './save.js';

const packSerial = player.backpack?.serial ?? die('arrows: no backpack to put them in');

// A wrong graphic is otherwise an afternoon of silence, so the count is the first thing said
log(`arrows: watching within ${GRAB_RANGE} tiles - ${describeFloor()} in the world`);

let stacks = 0;
let items = 0;
let quiet = 0;
let saidOutOfReach = false;
let stop: string | undefined;

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  // Before the sweep: everything attempted during a save is refused, and five of those in a row
  // would end the run on the quiet counter below
  if (isSaving()) {
    waitOutSave();
    quiet = 0;
    continue;
  }

  const reachable = inReach(onFloor(), GRAB_RANGE);

  // Deliberately not a stall: standing there with nothing in reach is the script waiting for you to
  // shoot, which is it working
  if (reachable.length === 0) {
    const floor = onFloor();
    const closest = nearest(floor);

    // Said once: a floor full of stacks that are all out of reach is indistinguishable from an empty
    // one from the log, and it is what a wrong GRAB_RANGE looks like
    if (closest !== undefined && !saidOutOfReach) {
      saidOutOfReach = true;
      log(
        `arrows: ${floor.length} on the floor, nearest ${closest} tiles away - ` +
          `nothing within ${GRAB_RANGE}, so nothing to take`,
      );
    }

    beat('watching', cycle, items);
    sleep(WATCH_POLL);
    continue;
  }

  sweep(packSerial, reachable);

  const took = settle(reachable, onFloor);
  stacks += took.stacks;
  items += took.items;

  if (took.stacks > 0) {
    quiet = 0;
    heartbeat.resetBeat();
    log(`arrows: took ${took.items} in ${took.stacks} stacks, ${items} in total`);
    continue;
  }

  // The pack full in a way packFull did not catch, or the client thinking a stack is closer than
  // the server does
  quiet++;

  if (quiet >= MAX_QUIET_SWEEPS) {
    stop = `${MAX_QUIET_SWEEPS} sweeps in a row moved nothing, with ${reachable.length} in reach`;
    break;
  }

  const backoff = backoffFor(quiet, SWEEP_BACKOFF, SWEEP_BACKOFF_MAX);
  log(`arrows: nothing moved (${quiet}/${MAX_QUIET_SWEEPS}), waiting ${backoff / 1000}s`);
  heartbeat.resetBeat();
  sleep(backoff);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;

log(`arrows: ${items} picked up in ${stacks} stacks`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`arrows: stopping - ${reason}`);
exit(`arrows: ${reason}`);
