import { collectIn, packContents } from '../lib/containers.js';
import { die } from '../lib/die.js';
import { dumpPack, hex, isKey } from './boxes.js';
import { LOG_EVERY_KEY, MAX_STUCK } from './config.js';
import { dropToGround } from './drop.js';

// Clears the keys already in the pack - the ones an earlier run put there before dropping worked.

const backpack = player.backpack ?? die('keys: no backpack');

// collectIn recurses, so this takes keys out of bags and out of any box still holding one
const keys = collectIn(packContents(), isKey);

if (keys.length === 0) {
  log('keys: nothing in the pack looks like a key.');
  dumpPack();
  die('keys: nothing to drop - put the right graphic in KEY_GRAPHICS in config.ts');
}

log(`keys: ${keys.length} keys in the pack, dropping them at your feet`);

let dropped = 0;
let running = 0;
const stuck: Item[] = [];
let stop: string | undefined;

for (const [index, key] of keys.entries()) {
  if (player.isDead) {
    stop = 'you are dead';
    break;
  }

  // Dropped from wherever it is: the pack for a loose key, the box for one still inside an open box
  if (dropToGround(key, key.container || backpack.serial)) {
    dropped++;
    running = 0;
  } else {
    stuck.push(key);
    running++;
  }

  // A key that will not go costs the whole DROP_TIMEOUT, so a shard that has stopped accepting them
  // would otherwise burn that on every remaining key
  if (running >= MAX_STUCK) {
    stop = `${running} keys in a row would not drop`;
    break;
  }

  // Without this a pile of keys is one line, a minute of nothing, then one more line - which is
  // indistinguishable from the script having hung
  if ((index + 1) % LOG_EVERY_KEY === 0) {
    log(`keys: ${dropped} down, ${keys.length - index - 1} to go`);
  }
}

if (stuck.length) {
  log(`keys: ${stuck.length} would not go: ${stuck.map((key) => hex(key.serial)).join(', ')}`);
}

log(`keys: ${dropped} of ${keys.length} on the floor`);

exit(`keys: ${stop ?? `dropped ${dropped}`}`);
