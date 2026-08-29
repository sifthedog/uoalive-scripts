import { backoffFor } from '../lib/loop.js';
import {
  CAST_DELAY,
  KEEP_UP,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_MISSES,
  MAX_THROTTLED,
  POLL,
  SET_ASIDE,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { beat } from './heartbeat.js';
import {
  armed,
  castOnce,
  due,
  retire,
  roster,
  setAside,
  settled,
  spent,
  standing,
  type Kept,
} from './keep.js';
import { isSaving, waitOutSave } from './save.js';

const PREFIX = 'buffs';

const table = roster();

let casts = 0;
let reported = 0;
let throttled = 0;
let stop: string | undefined;

// Said once per stretch rather than once per pass, or an unarmed character scrolls the journal at
// POLL for as long as they stay unarmed
let saidUnarmed = false;
let saidShort = false;

const proved = new Set<string>();

// The first cast of each spell, so a wrong OUTCOME_TEXT or a wrong buff id shows up in the first
// minute rather than as a run that quietly never casts
const sayFirst = (item: Kept): void => {
  if (proved.has(item.name)) {
    return;
  }

  proved.add(item.name);
  log(`${PREFIX}: ${item.name} up`);
};

const backOff = (): void => {
  throttled++;

  if (throttled >= MAX_THROTTLED) {
    stop = `the shard refused ${MAX_THROTTLED} casts in a row`;

    return;
  }

  sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
};

const landed = (item: Kept): void => {
  casts++;
  throttled = 0;
  item.misses = 0;
  sayFirst(item);
};

const putUp = (item: Kept): void => {
  const outcome = castOnce(item.entry);

  switch (outcome) {
    case 'cast':
      landed(item);
      break;

    // The shard answered, so the table is right and the roll simply lost. Next pass tries again.
    case 'fizzled':
    case 'alreadyUp':
      throttled = 0;
      item.misses = 0;
      break;

    // The gate above cleared, so this entry's mana figure is understated for this shard
    case 'noMana':
      item.misses = 0;
      log(`${PREFIX}: ${item.name} costs more than ${item.entry.mana} mana here - raise it in KEEP`);
      break;

    // Nothing a script does refills tithing points, so this entry is finished for the run
    case 'noTithing':
      retire(item, 'out of tithing points - tithe gold at a shrine');
      break;

    case 'unskilled':
      retire(item, 'the shard refuses it at this skill or karma');
      break;

    // The hand check above missed it, so believe the shard rather than the client's layers
    case 'noWeapon':
      setAside(item, SET_ASIDE);
      break;

    case 'saving':
      waitOutSave();
      break;

    case 'cooldown':
    case 'throttled':
    case 'alreadyCasting':
      backOff();
      break;

    // Nothing said, no buff, and no mana left the pool: whatever this was, it did not happen
    default:
      item.misses++;

      if (item.misses >= MAX_MISSES) {
        setAside(item, SET_ASIDE);
        log(`${PREFIX}: ${item.name} did nothing ${MAX_MISSES} times - set aside; check OUTCOME_TEXT`);
      }
  }
};

const pass = (): void => {
  const hands = armed();

  if (hands) {
    saidUnarmed = false;
  }

  for (const item of table) {
    if (stop || !due(item)) {
      continue;
    }

    if (standing(item.entry)) {
      item.misses = 0;
      continue;
    }

    if (item.entry.needsWeapon && !hands) {
      if (!saidUnarmed) {
        saidUnarmed = true;
        log(`${PREFIX}: nothing in hand - ${item.name} is waiting for you to draw something`);
      }

      continue;
    }

    if (player.mana < item.entry.mana) {
      if (!saidShort) {
        saidShort = true;
        log(`${PREFIX}: ${player.mana}/${item.entry.mana} mana for ${item.name} - waiting for it`);
      }

      continue;
    }

    saidShort = false;
    putUp(item);
    sleep(CAST_DELAY);
  }
};

log(`${PREFIX}: keeping ${table.map((item) => item.name).join(' and ')} up`);

if (!armed() && table.some((item) => item.entry.needsWeapon)) {
  log(`${PREFIX}: nothing in hand - the weapon enchants will be refused until you draw something`);
}

// The client publishes no tithing stat, so this is a reminder rather than a check
log(`${PREFIX}: every cast spends tithing points; tithe gold at a shrine before a long run`);

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();

  if (stop) {
    break;
  }

  if (isSaving()) {
    waitOutSave();
    continue;
  }

  pass();

  if (stop) {
    break;
  }

  if (spent(table)) {
    stop = 'every buff was refused for good';
    break;
  }

  if (!KEEP_UP && settled(table)) {
    stop = 'everything that could go up is up';
    break;
  }

  if (casts >= reported + LOG_EVERY) {
    reported = casts;
    log(`${PREFIX}: ${casts} casts, ${player.mana}/${player.maxMana} mana`);
  }

  beat('watching the buff bar', cycle, casts);
  sleep(POLL);
}

for (const item of table) {
  if (item.retired) {
    log(`${PREFIX}: ${item.name} was set aside - ${item.retired}`);
  }
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;

log(`${PREFIX}: ${casts} casts, stopping - ${reason}`);
exit(`${PREFIX}: ${reason}`);
