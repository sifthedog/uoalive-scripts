// Necromancy on src/lib/trainer.ts, the same loop src/training/ runs Bushido on. Three differences,
// all settled in config.ts: three of the five bands are transformations, which stand until re-cast
// rather than expiring, so the toggle back off is counted as the cast it is; one band is cast at the
// character and one drains it, so there is a health floor and the run bandages itself at it; and
// nothing is ever held, so unlike the weapon trainer no stow is needed.

import { createCaster } from '../lib/cast.js';
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
import { restore, stow, stripMore, survey } from './gear.js';
import { stopReason } from './guards.js';
import { mend } from './heal.js';
import { beat, resetBeat } from './heartbeat.js';
import { waitOutSave } from './save.js';

const PREFIX = 'necro';

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

// This run puts nothing in the character's hands, so what the strip is for is the armour - and that
// only ever comes off on a shard that refuses a trance for it. See ./gear.ts.
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
  disabledIsProgress: DISABLED_IS_PROGRESS,
  stopReason,
  recover: mend,
  beat,
  waitOutSave,

  preflight: () => {
    log(
      `${PREFIX}: ${player.hits}/${player.maxHits} hits, ${player.mana}/${player.maxMana} mana`,
    );

    // Reported rather than warned about, now that the run takes these off and puts the same items
    // back. Said at start-up because it is also the line that catches a client whose findItemOnLayer
    // does not answer for the player: an empty survey on a dressed character means nothing will ever
    // be stripped and the run will quietly fall back on natural regeneration.
    log(`${PREFIX}: ${survey()}`);

    // Said now rather than discovered at the floor, which on the Lich Form band is an hour in
    if (BANDAGE && !client.findType(BANDAGE_GRAPHIC, undefined, player.backpack?.serial)) {
      log(`${PREFIX}: no bandages in the pack - the health floor will stop the run instead`);
    }
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
