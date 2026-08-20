import { die } from '../lib/die.js';
import { hex } from '../lib/entity.js';
import { type Picked, pickMany, pickOne } from '../lib/pick.js';
import { LOG_EVERY_ITEM, MAX_PICKS, OPEN_DELAY, OPL_TIMEOUT } from './config.js';
import { artKey, transfer, wantedFrom } from './move.js';

const name = (picked: Picked): string => `${picked.name || artKey(picked)} (${hex(picked.serial)})`;

const source =
  pickOne({ prefix: 'transfer', prompt: 'target the container to empty', oplTimeout: OPL_TIMEOUT }) ??
  die('transfer: no container to empty');

const destination =
  pickOne({ prefix: 'transfer', prompt: 'target the container to fill', oplTimeout: OPL_TIMEOUT }) ??
  die('transfer: nowhere to put it');

if (destination.serial === source.serial) {
  die('transfer: that is the same container twice');
}

const picks = pickMany({
  prefix: 'transfer',
  prompt: 'target one of each item to move, ESC to move all of it',
  maxPicks: MAX_PICKS,
  oplTimeout: OPL_TIMEOUT,
  keyOf: artKey,
  label: (picked) => `${picked.name || 'unnamed'} ${artKey(picked)}`,
});

const wanted = wantedFrom(picks);

log(`transfer: ${name(source)} -> ${name(destination)}, moving ${wanted.describe()}`);

// The destination is opened too: the client drops into a container window, not into a serial
player.use(destination.serial);
sleep(OPEN_DELAY);

const { outcome, stacks, items, left } = transfer(
  source.serial,
  destination.serial,
  wanted,
  (item) => {
    if (LOG_EVERY_ITEM) {
      log(`transfer:   ${artKey(item)} x${item.amount ?? 1}`);
    }
  },
);

const tally = `${stacks} stacks, ${items} items`;

const reason =
  outcome === 'emptied'
    ? `moved ${tally}`
    : outcome === 'unopened'
      ? `${hex(source.serial)} would not open - stand closer, or open it yourself first`
      : `${left} left behind, nothing moved on the last pass - moved ${tally}`;

exit(`transfer: ${reason}`);
