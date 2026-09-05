import { die } from '../lib/die.js';
import { backoffFor } from '../lib/loop.js';
import {
  GRAB_RANGE,
  MAX_CYCLES,
  MAX_QUIET_SWEEPS,
  PRUNE_EVERY,
  SWEEP_BACKOFF,
  SWEEP_BACKOFF_MAX,
  WATCH_POLL,
} from './config.js';
import { describeFloor, inReach, nearest, onFloor, prune, setAside } from './floor.js';
import { describeTake, settle, sweep } from './grab.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { isSaving, waitOutSave } from './save.js';

const packSerial = player.backpack?.serial ?? die('sweep: no backpack to put them in');

// A wrong graphic is otherwise an afternoon of silence, so the count is the first thing said
log(`sweep: watching within ${GRAB_RANGE} tiles - ${describeFloor()} in the world`);

let stacks = 0;
let items = 0;
let coins = 0;
let quiet = 0;
let waits = 0;
let saidOutOfReach = false;
let stop: string | undefined;

// Discounted from the backstop below, which bounds sweeps: watching an empty floor used to spend the
// whole budget standing still, and end a run eight minutes in
let idled = 0;

try {
  for (let cycle = 0; cycle - idled < MAX_CYCLES && !stop; cycle++) {
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

    const floor = onFloor();
    const reachable = inReach(floor, GRAB_RANGE);

    // Deliberately not a stall: standing there with nothing in reach is the script waiting for you to
    // shoot, which is it working
    if (reachable.length === 0) {
      const closest = nearest(floor);

      // Said once: a floor full of stacks that are all out of reach is indistinguishable from an empty
      // one from the log, and it is what a wrong GRAB_RANGE looks like
      if (closest !== undefined && !saidOutOfReach) {
        saidOutOfReach = true;
        log(
          `sweep: ${floor.length} on the floor, nearest ${closest} tiles away - ` +
            `nothing within ${GRAB_RANGE}, so nothing to take`,
        );
      }

      // Only on the idle path, and only every so often: this is a findObject per blocked serial, and
      // the map only grows while the script has nothing else to do anyway.
      if (++waits % PRUNE_EVERY === 0) {
        prune();
      }

      idled++;
      quiet = 0;
      beat('watching', cycle, stacks);
      sleep(WATCH_POLL);
      continue;
    }

    saidOutOfReach = false;

    sweep(packSerial, reachable);

    const took = settle(reachable, onFloor);
    stacks += took.stacks;
    items += took.items;
    coins += took.coins;

    if (took.stacks > 0) {
      quiet = 0;
      heartbeat.resetBeat();
      log(
        `sweep: took ${describeTake(took)} in ${took.stacks} stacks ` +
          `(${describeTake({ items, coins })} so far)`,
      );
      continue;
    }

    // The pack full in a way packFull did not catch, or the client thinking a stack is closer than
    // the server does. Set aside rather than swept again, so one stack the server will not move
    // cannot walk the run to the stop below a cycle at a time.
    quiet++;
    setAside(reachable);

    if (quiet >= MAX_QUIET_SWEEPS) {
      stop = `${MAX_QUIET_SWEEPS} sweeps in a row moved nothing, with ${reachable.length} in reach`;
      break;
    }

    const backoff = backoffFor(quiet, SWEEP_BACKOFF, SWEEP_BACKOFF_MAX);
    log(`sweep: nothing moved (${quiet}/${MAX_QUIET_SWEEPS}), waiting ${backoff / 1000}s`);
    heartbeat.resetBeat();
    sleep(backoff);
  }
} catch (error) {
  // Nothing else catches: a throw out of a client call used to end the run with no line at all
  stop ??= `threw - ${String(error)}`;
}

const reason = stop ?? `hit the ${MAX_CYCLES} working cycle backstop`;

log(`sweep: ${describeTake({ items, coins })} picked up in ${stacks} stacks`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`sweep: stopping - ${reason}`);
exit(`sweep: ${reason}`);
