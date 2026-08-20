import { die } from '../lib/die.js';
import { nameOf } from '../lib/entity.js';
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { pickOne } from '../lib/pick.js';
import { createSkillReader, tenths } from '../lib/skill.js';
import { pickOnce, STOP_REASON } from './attempt.js';
import {
  ATTEMPT_DELAY,
  GOAL,
  LOG_EVERY,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_NO_CURSOR,
  MAX_THROTTLED,
  OPL_TIMEOUT,
  SKILL_POLL,
  SKILL_TIMEOUT,
  STALL_STOP,
  STALL_WARN,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { findLockpick, lockpickTotal } from './picks.js';
import { isSaving, waitOutSave } from './save.js';

const box =
  pickOne({
    prefix: 'lockpick',
    prompt: 'target the locked container to pick',
    oplTimeout: OPL_TIMEOUT,
  }) ?? die('lockpick: nothing to pick');

const skill = createSkillReader({
  skill: Skills.Lockpicking,
  label: 'Lockpicking',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const start = skill.waitForSkill() ?? die('lockpick: the client is not reporting the skill');

log(
  `lockpick: ${nameOf(box)} - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}, ` +
    `${lockpickTotal()} lockpicks`,
);

// Said rather than corrected: a power scroll may be on its way, and a run that quietly retargeted
// itself would be lying about its goal.
const cap = skill.cap();

if (cap !== undefined && GOAL > cap) {
  log(`lockpick: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
}

const stall = createStallWatch({
  prefix: 'lockpick',
  without: 'cycles without an attempt',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

let attempts = 0;
let broken = 0;
let throttled = 0;
let noCursor = 0;
let blind = 0;
let reported = 0;
let lastValue = start;
let stop: string | undefined;

// Reported at the end so a wrong OUTCOME_TEXT is still obvious, but never a reason to stop: whether
// the run is getting anywhere is a separate question from whether it can follow along.
let unread = 0;

// The ones since the skill last moved, credited to the tally when it does
let unreadPending = 0;

// Said once per stretch rather than once per attempt, so a real ending does not scroll away
let unreadSaid = false;

const cleared = (): void => {
  unreadSaid = false;
  throttled = 0;
  noCursor = 0;
};

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  // Before anything else: during a save every attempt is refused, and each refusal would be charged
  // to a counter that ends the run.
  if (isSaving()) {
    waitOutSave();
    cleared();
    stall.progressed();
    stall.endCycle('saving', cycle, attempts);
    continue;
  }

  const value = skill.value();

  // Never read as 0, which would be a real skill value and would hide a character who is already done
  if (value === undefined) {
    blind++;

    if (blind >= MAX_BLIND_READS) {
      stop = 'the client stopped reporting the skill';
      break;
    }

    beat('unreadable skill', cycle, attempts);
    sleep(ATTEMPT_DELAY);
    continue;
  }

  blind = 0;

  // The one signal no wording can argue with: if the number moved, the picking is working, whatever
  // the journal looked like from in here.
  if (value !== lastValue) {
    lastValue = value;
    attempts += unreadPending;
    unreadPending = 0;
    unreadSaid = false;
    stall.progressed();
  }

  if (value >= GOAL) {
    stop = `${skill.name()} is at ${tenths(value)}`;
    break;
  }

  const lockpick = findLockpick();

  if (!lockpick) {
    stop = 'out of lockpicks';
    break;
  }

  const outcome = pickOnce(box.serial, lockpick.serial);

  if (outcome !== 'throttled') {
    throttled = 0;
  }

  if (outcome !== 'noCursor') {
    noCursor = 0;
  }

  switch (outcome) {
    // Both rolled the skill, which is the whole of the training
    case 'broke':
    case 'failed':
      attempts++;
      unreadSaid = false;
      stall.progressed();

      if (outcome === 'broke') {
        broken++;
      }
      break;

    case 'saving':
      waitOutSave();
      cleared();
      stall.progressed();
      break;

    case 'throttled':
      throttled++;
      log(`lockpick: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the attempt';
      }
      break;

    case 'noCursor':
      noCursor++;
      log(`lockpick: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
      sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (noCursor >= MAX_NO_CURSOR) {
        stop = 'the shard never opened a target cursor';
      }
      break;

    default: {
      const terminal = outcome && STOP_REASON[outcome];

      if (terminal) {
        stop = terminal;
        break;
      }

      unread++;
      unreadPending++;

      if (!unreadSaid) {
        unreadSaid = true;
        log('lockpick: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls');
      }
    }
  }

  if (attempts >= reported + LOG_EVERY) {
    reported = attempts;
    log(
      `lockpick: ${attempts} attempts, ${broken} broken, ${lockpickTotal()} left, ` +
        `${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`,
    );
  }

  stall.endCycle(outcome ?? 'unknown', cycle, attempts);
  stop = stop ?? stall.reason();
  sleep(ATTEMPT_DELAY);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
const ended = skill.value();

log(
  `lockpick: ${attempts} attempts, ${broken} lockpicks broken, ${skill.name()} ${tenths(start)} -> ` +
    `${ended === undefined ? 'unknown' : tenths(ended)}`,
);

// Said only when there were any, and said last so it reads as the footnote it is
if (unread > 0) {
  log(`lockpick: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
}

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended must not be the line that gets away
log(`lockpick: stopping - ${reason}`);
exit(`lockpick: ${reason}`);
