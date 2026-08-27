import { CONTAINER_GRAPHICS } from '../lib/containers.js';
import { die } from '../lib/die.js';
import { hex, isMobile } from '../lib/entity.js';
import { backoffFor } from '../lib/loop.js';
import { type Picked, pickMany, pickOne } from '../lib/pick.js';
import { artKey, wantedFrom } from '../lib/sift.js';
import {
  LOG_EVERY_ITEM,
  MAX_CYCLES,
  MAX_LOST_DEST,
  MAX_PICKS,
  MAX_QUIET_STOWS,
  OPEN_DELAY,
  OPL_TIMEOUT,
  STOW_BACKOFF,
  STOW_BACKOFF_MAX,
  WATCH_POLL,
} from './config.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { issue, settle, type Took } from './move.js';
import { isSaving, waitOutSave } from './save.js';
import { createScan } from './scan.js';
import { createQuiet, verdictFor } from './tally.js';

const NOTHING: Took = { stacks: 0, items: 0 };

const packSerial = player.backpack?.serial ?? die('stow: no backpack to watch');

const picks = pickMany({
  prefix: 'stow',
  prompt: 'target one of each item to stow, ESC when done',
  maxPicks: MAX_PICKS,
  oplTimeout: OPL_TIMEOUT,
  keyOf: artKey,
  label: (picked) => `${picked.name || 'unnamed'} ${artKey(picked)}`,
});

// Zero art matches nothing, so one left on the list would sit there unstowed behind a filter it can
// never satisfy
for (const unknown of picks.filter((picked) => picked.graphic === 0)) {
  log(
    `stow: nothing knows the art of '${unknown.name}', so it cannot be matched - ` +
      'hover it and run again',
  );
}

const watched = picks.filter((picked) => picked.graphic !== 0);

if (watched.length === 0) {
  // Not transfer's 'everything': a watcher matching everything would empty your regs and your
  // unequipped kit into a chest in the background for hours
  die('stow: nothing to watch');
}

const destination =
  pickOne({
    prefix: 'stow',
    prompt: 'target the container to stow them in',
    oplTimeout: OPL_TIMEOUT,
  }) ??
  die('stow: nowhere to put it');

if (destination.serial === packSerial) {
  die('stow: that is the backpack itself - pick a bag or a chest to stow into');
}

if (watched.some((picked) => picked.serial === destination.serial)) {
  die('stow: the container is one of the items to stow');
}

for (const bag of watched.filter((picked) => CONTAINER_GRAPHICS.has(picked.graphic))) {
  log(`stow: '${bag.name || 'unnamed'}' ${artKey(bag)} is a container, so it goes across whole`);
}

const wanted = wantedFrom(watched);
const scan = createScan({ destSerial: destination.serial, wanted });
const quiet = createQuiet(MAX_QUIET_STOWS);

const name = (picked: Picked): string => `${picked.name || artKey(picked)} (${hex(picked.serial)})`;

// The client drops into a container window, not into a serial
player.use(destination.serial);
sleep(OPEN_DELAY);

const here = (): boolean => {
  const found = client.findObject(destination.serial);

  return !!found && !isMobile(found);
};

log(
  `stow: watching ${watched.map((picked) => artKey(picked)).join(', ')} -> ${name(destination)}`,
);

let stacks = 0;
let items = 0;
let lost = 0;
let saidLost = false;
let stop: string | undefined;

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  // Before the scan: everything attempted during a save is refused, and a save long enough would
  // end the run on the quiet counter below
  if (isSaving()) {
    waitOutSave();
    quiet.reset();
    continue;
  }

  if (!here()) {
    lost++;

    if (lost >= MAX_LOST_DEST) {
      stop =
        `${hex(destination.serial)} has not been where the client can see it for ${lost} polls`;
      break;
    }

    // Said once: riding two screens away and back is normal, and a line per poll would bury the run
    if (!saidLost) {
      saidLost = true;
      log(
        `stow: ${name(destination)} is not where the client can see it, ` +
          'waiting for it to come back',
      );
      heartbeat.resetBeat();
    }

    sleep(WATCH_POLL);
    continue;
  }

  if (saidLost) {
    saidLost = false;
    lost = 0;
    log(`stow: ${name(destination)} is back`);

    // Also the recovery for a container window closed by hand, which reads the same from here
    player.use(destination.serial);
    sleep(OPEN_DELAY);
    heartbeat.resetBeat();
  }

  const found = scan.look();

  // packContents never latches, so a backpack that would not answer is transient rather than a
  // reason to count anything against the run
  if (!found.readable) {
    beat('waiting for the pack', cycle, items);
    sleep(WATCH_POLL);
    continue;
  }

  if (scan.openNew(found.containers)) {
    continue;
  }

  const todo = scan.wantedIn(found);

  if (LOG_EVERY_ITEM) {
    for (const item of todo) {
      log(`stow:   ${artKey(item)} x${item.amount ?? 1}`);
    }
  }

  const sent = issue(todo, destination.serial);
  const took = sent.length > 0 ? settle(sent, () => scan.wantedIn(scan.look())) : NOTHING;

  stacks += took.stacks;
  items += took.items;

  const verdict = verdictFor(sent.length, took.stacks);
  const misses = quiet.saw(verdict);

  if (verdict === 'idle') {
    beat('watching', cycle, items);
    sleep(WATCH_POLL);
    continue;
  }

  if (verdict === 'moved') {
    heartbeat.resetBeat();
    log(`stow: stowed ${took.items} in ${took.stacks} stacks, ${items} in total`);
    continue;
  }

  stop = quiet.reason(todo.length);
  if (stop) {
    break;
  }

  // The destination full, out of reach, or the shard refusing in silence - indistinguishable from
  // here, since moveItem reports only that the packet went out
  const backoff = backoffFor(misses, STOW_BACKOFF, STOW_BACKOFF_MAX);
  log(`stow: nothing moved (${misses}/${MAX_QUIET_STOWS}), waiting ${backoff / 1000}s`);
  heartbeat.resetBeat();
  sleep(backoff);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;

log(`stow: ${items} stowed in ${stacks} stacks`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`stow: stopping - ${reason}`);
exit(`stow: ${reason}`);
