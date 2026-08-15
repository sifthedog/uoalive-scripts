// Bushido on src/lib/trainer.ts. The table in config.ts is the whole policy, so another skill is
// another table rather than another script - src/necromancy/ is this loop with a different one.
//
// The two halves of this run want opposite things from the character's hands: these are weapon
// abilities, and meditation is refused while anything is equipped. See weapon.ts.

import { createCaster } from '../lib/cast.js';
import { describeItem } from '../lib/entity.js';
import { createManaWait } from '../lib/meditate.js';
import { createSkillReader } from '../lib/skill.js';
import { runTrainer } from '../lib/trainer.js';
import {
  BUFF_WAIT,
  CASTING_WAIT,
  CAST_DELAY,
  CAST_TIMEOUT,
  COOLDOWN_BACKOFF,
  COOLDOWN_BACKOFF_MAX,
  LOG_EVERY,
  MANA_LOG_EVERY,
  MANA_POLL,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_THROTTLED,
  MAX_STALE,
  MEDITATE,
  MEDITATE_ATTEMPTS,
  MEDITATE_OUTCOME_TEXT,
  MEDITATE_START_TIMEOUT,
  MEDITATE_TIMEOUT,
  MEDITATE_TO_FULL,
  OUTCOME_TEXT,
  REGEN_TIMEOUT,
  SKILL,
  SKILL_LABEL,
  SKILL_POLL,
  SKILL_TIMEOUT,
  SKIP_WHEN_BUFFED,
  STAGES,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { restore, stow, stripMore, survey } from './gear.js';
import { beat, resetBeat } from './heartbeat.js';
import { waitOutSave } from './save.js';
import { held, rearm, rememberWeapon } from './weapon.js';

const PREFIX = 'train';

const skill = createSkillReader({
  skill: SKILL,
  label: SKILL_LABEL,
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const { castOnce } = createCaster({
  outcomeText: OUTCOME_TEXT,
  timeoutMs: CAST_TIMEOUT,
  skipWhenBuffed: SKIP_WHEN_BUFFED,
});

const mana = createManaWait({
  prefix: PREFIX,
  outcomeText: MEDITATE_OUTCOME_TEXT,
  meditate: MEDITATE,
  toFull: MEDITATE_TO_FULL,
  timeoutMs: MEDITATE_TIMEOUT,
  attempts: MEDITATE_ATTEMPTS,
  startTimeoutMs: MEDITATE_START_TIMEOUT,
  pollMs: MANA_POLL,
  logEveryMs: MANA_LOG_EVERY,
  regenTimeoutMs: REGEN_TIMEOUT,
  // ./gear.ts and no longer ./weapon.ts. The weapon still comes off for every trance, but it goes
  // back on by the serial that came off rather than by graphic - so a weapon with properties on it
  // returns as itself - and the shield or armour this shard may also refuse comes off with it.
  stow,
  restore,
  stripMore,
  stopReason,
  resetBeat,
  waitOutSave,
});

runTrainer({
  prefix: PREFIX,
  stages: STAGES,
  skill,
  castOnce,
  regainMana: mana.regainMana,
  manaBlocked: mana.blocked,
  rearm,
  stopReason,
  beat,
  waitOutSave,

  preflight: () => {
    // Learned from what is in hand, so the draw after each trance matches on this weapon's graphic
    // rather than on whatever WEAPON_NAME finds in the pack
    const weapon = held();
    rememberWeapon(weapon);

    log(`${PREFIX}: hand ${describeItem(weapon)}, ${player.mana}/${player.maxMana} mana`);

    if (!weapon) {
      log(`${PREFIX}: nothing in hand - these are weapon abilities, so the first cast may be refused`);
    }

    // Also the line that catches a client whose findItemOnLayer does not answer for the player: an
    // empty survey on a dressed character means nothing will ever be stripped
    log(`${PREFIX}: ${survey()}`);
  },

  timings: {
    castDelay: CAST_DELAY,
    castTimeout: CAST_TIMEOUT,
    buffWait: BUFF_WAIT,
    castingWait: CASTING_WAIT,
    stepDelay: STEP_DELAY,
    maxCycles: MAX_CYCLES,
    maxBlindReads: MAX_BLIND_READS,
    regenTimeout: REGEN_TIMEOUT,
    maxThrottled: MAX_THROTTLED,
    maxStale: MAX_STALE,
    logEvery: LOG_EVERY,
    cooldownBackoff: COOLDOWN_BACKOFF,
    cooldownBackoffMax: COOLDOWN_BACKOFF_MAX,
    throttleBackoff: THROTTLE_BACKOFF,
    throttleBackoffMax: THROTTLE_BACKOFF_MAX,
  },
});
