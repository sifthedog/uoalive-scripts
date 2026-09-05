import { die } from '../lib/die.js';
import { hex } from '../lib/entity.js';
import {
  CORPSE_GRAPHIC,
  LOG_ITEMS,
  MAX_OPL_ASKS,
  OPEN_DELAY,
  OPEN_RANGE,
  OPL_TIMEOUT,
  SCAN_RANGE,
  SETTLE_POLL,
  SETTLE_TIMEOUT,
} from './config.js';
import { chooseMine, describeGround, inRange, nearest, onGround, survey } from './corpses.js';
import { describeHeld, open } from './open.js';

const me = (player.name ?? '').trim();

if (!me) {
  log('corpse: the client has not said your name yet, so this can only take the nearest');
}

const all = onGround();

log(`corpse: looking for '${me || 'anyone'}' within ${SCAN_RANGE} tiles - ${describeGround(all)}`);

if (all.length === 0) {
  die(
    'corpse: no corpses anywhere the client can see - if yours is on screen, ' +
      `${hex(CORPSE_GRAPHIC)} is not this shard's corpse art`,
  );
}

const near = inRange(all, SCAN_RANGE);

if (near.length === 0) {
  die(
    `corpse: ${all.length} in the world, nearest ${nearest(all)} tiles away - ` +
      `nothing within ${SCAN_RANGE}`,
  );
}

const candidates = survey(near, MAX_OPL_ASKS, OPL_TIMEOUT);
const choice = chooseMine(candidates, me) ?? die('corpse: nothing to open');
const { picked, why, named } = choice;
const label = picked.name || hex(picked.serial);

if (why === 'nearest') {
  const unnamed = candidates.filter((one) => !one.name).length;

  // The unnamed count is what tells a ghost with no tooltip data apart from a field of monster
  // corpses - both otherwise print as 'nothing here is named for you'
  log(
    `corpse: nothing here is named for you` +
      (unnamed ? ` (${unnamed} of ${candidates.length} would not say what they are)` : '') +
      ` - taking the nearest, '${label}' (${hex(picked.serial)}), ${picked.distance} tiles away`,
  );
} else {
  log(
    `corpse: '${picked.name}' (${hex(picked.serial)}) is yours, ` +
      `${picked.distance} tiles away - ${why} name match`,
  );

  if (named > 1) {
    log(`corpse: ${named} corpses here are named for you, taking the nearest`);
  }
}

// After the choice and never before it: a corpse at your feet must not be able to displace the one
// that carries your name
if (picked.distance > OPEN_RANGE) {
  const other = candidates.find(
    (one) => one.distance <= OPEN_RANGE && one.serial !== picked.serial,
  );

  die(
    other
      ? `corpse: yours is ${picked.distance} tiles away, and '${other.name || hex(other.serial)}' ` +
          `in reach is not yours - walk to yours and run it again`
      : `corpse: ${hex(picked.serial)} is ${picked.distance} tiles away - ` +
          `walk within ${OPEN_RANGE} and run it again`,
  );
}

const { outcome, contents } = open(picked.serial, {
  openDelay: OPEN_DELAY,
  settlePoll: SETTLE_POLL,
  settleTimeout: SETTLE_TIMEOUT,
});

if (outcome === 'gone') {
  die(`corpse: ${hex(picked.serial)} is no longer there - it decayed, or someone moved it`);
}

// containers.ts has already logged the throw itself, so this says what to do rather than what broke
if (outcome === 'unreadable') {
  die(
    `corpse: ${hex(picked.serial)} would not say what it holds - the window may be up anyway; ` +
      'stand on it and run it again',
  );
}

if (outcome === 'empty') {
  die(`corpse: '${label}' is open and reports nothing in it`);
}

log(`corpse: '${label}' holds ${describeHeld(contents, LOG_ITEMS)}`);

const items = contents.reduce((total, one) => total + (one.amount ?? 1), 0);

exit(`corpse: opened ${hex(picked.serial)} - ${contents.length} stacks, ${items} items`);
