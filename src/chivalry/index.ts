// Chivalry on src/lib/trainer.ts, the same loop src/training/ and src/necromancy/ run on.
//
// Two things are particular to a paladin. Every cast spends tithing points as well as mana, and
// tithing is gold given at a shrine - so running out is an ending rather than a wait. And only the
// first band wants a weapon, so a run that starts armed stows for every trance and draws again
// afterwards, while one that starts empty-handed never touches any of that.

import { createCaster } from '../lib/cast.js';
import { describeItem } from '../lib/entity.js';
import { createManaWait } from '../lib/meditate.js';
import { createSkillReader } from '../lib/skill.js';
import { runTrainer } from '../lib/trainer.js';
import {
  BANDAGE,
  BANDAGE_GRAPHIC,
  BUFF_WAIT,
  CASTING_WAIT,
  CAST_DELAY,
  CAST_TIMEOUT,
  COOLDOWN_BACKOFF,
  COOLDOWN_BACKOFF_MAX,
  DISABLED_IS_PROGRESS,
  LOG_EVERY,
  MANA_LOG_EVERY,
  MANA_POLL,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_HUNGRY,
  MAX_THROTTLED,
  MAX_UNKNOWN,
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
import { mend } from './heal.js';
import { restore, stow, stripMore, survey } from './gear.js';
import { beat, resetBeat } from './heartbeat.js';
import { waitOutSave } from './save.js';
import { held, rearm, rememberWeapon } from './weapon.js';

const PREFIX = 'chiv';

// Decided once, from what is actually in hand. An unconditional draw on a character who never held
// anything finds nothing in the pack and ends a run that was training Divine Fury perfectly well.
const weapon = held();
const armed = weapon !== undefined;

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
  // Unconditional where the weapon half below is not: gear only ever puts back what it took, so an
  // empty-handed paladin has nothing in hand to restore and never attempts the draw that `armed`
  // exists to prevent. It also means an unarmed but armoured character is undressed for the trance,
  // which the weapon-only version could not do.
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
  rearm: armed ? rearm : undefined,
  disabledIsProgress: DISABLED_IS_PROGRESS,
  stopReason,
  recover: mend,
  beat,
  waitOutSave,

  preflight: () => {
    // Learned from what is in hand, so the draw after each trance matches on this weapon's graphic
    // rather than on whatever WEAPON_NAME finds in the pack
    rememberWeapon(weapon);

    log(
      `${PREFIX}: hand ${describeItem(weapon)}, ${player.hits}/${player.maxHits} hits, ` +
        `${player.mana}/${player.maxMana} mana`,
    );

    if (!armed) {
      log(`${PREFIX}: nothing in hand - Consecrate Weapon will be refused, the other bands will not`);
    }

    // Also the line that catches a client whose findItemOnLayer does not answer for the player: an
    // empty survey on a dressed character means nothing will ever be stripped
    log(`${PREFIX}: ${survey()}`);

    // Said now rather than discovered at the floor, which on the last band is an hour in
    if (BANDAGE && !client.findType(BANDAGE_GRAPHIC, undefined, player.backpack?.serial)) {
      log(`${PREFIX}: no bandages in the pack - the health floor will stop the run instead`);
    }

    // The client publishes no tithing stat, so this is a reminder rather than a check
    log(`${PREFIX}: every cast spends tithing points; tithe gold at a shrine before a long run`);
  },

  timings: {
    castDelay: CAST_DELAY,
    buffWait: BUFF_WAIT,
    castingWait: CASTING_WAIT,
    stepDelay: STEP_DELAY,
    maxCycles: MAX_CYCLES,
    maxBlindReads: MAX_BLIND_READS,
    maxHungry: MAX_HUNGRY,
    maxThrottled: MAX_THROTTLED,
    maxUnknown: MAX_UNKNOWN,
    logEvery: LOG_EVERY,
    cooldownBackoff: COOLDOWN_BACKOFF,
    cooldownBackoffMax: COOLDOWN_BACKOFF_MAX,
    throttleBackoff: THROTTLE_BACKOFF,
    throttleBackoffMax: THROTTLE_BACKOFF_MAX,
  },
});
