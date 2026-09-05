import { die } from '../lib/die.js';
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { createPace } from '../lib/pace.js';
import { createSkillReader, tenths } from '../lib/skill.js';
import {
  GOAL,
  LOG_EVERY,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_THROTTLED,
  PACE_EASE_AFTER,
  PACE_MAX,
  PACE_STEP,
  SKILL_POLL,
  SKILL_TIMEOUT,
  STALL_STOP,
  STALL_WARN,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  USE_DELAY,
} from './config.js';
import { evaluateOnce, STOP_REASON } from './evaluate.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { isSaving, waitOutSave } from './save.js';

const skill = createSkillReader({
  skill: Skills.EvalInt,
  label: 'Evaluating Intelligence',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const start = skill.waitForSkill() ?? die('evalint: the client is not reporting the skill');

log(`evalint: reading yourself - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}`);

// Said rather than corrected: a power scroll may be on its way, and a run that quietly retargeted
// itself would be lying about its goal.
const cap = skill.cap();

if (cap !== undefined && GOAL > cap) {
  log(`evalint: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
}

const pace = createPace({ floor: USE_DELAY, step: PACE_STEP, max: PACE_MAX, easeAfter: PACE_EASE_AFTER });

const stall = createStallWatch({
  prefix: 'evalint',
  without: 'cycles without a read',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

let reads = 0;
let missed = 0;
let throttled = 0;
let blind = 0;
let reported = 0;
let lastValue = start;
let stop: string | undefined;

// Reported at the end so a wrong OUTCOME_TEXT is still obvious, but never a reason to stop: whether
// the run is getting anywhere is a separate question from whether it can follow along.
let unread = 0;

// The ones since the skill last moved, credited to the tally when it does
let unreadPending = 0;

// Said once per stretch rather than once per cycle, so a real ending does not scroll away
let unreadSaid = false;

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();

  if (stop) {
    break;
  }

  // Before anything else: during a save every read is refused, and each refusal would be charged to
  // a counter that ends the run.
  if (isSaving()) {
    waitOutSave();
    throttled = 0;
    unreadSaid = false;
    stall.progressed();
    stall.endCycle('saving', cycle, reads);
    continue;
  }

  const value = skill.value();

  // Never read as 0, which would be a real skill value and would hide a character already done
  if (value === undefined) {
    blind++;

    if (blind >= MAX_BLIND_READS) {
      stop = 'the client stopped reporting the skill';
      break;
    }

    beat('unreadable skill', cycle, reads);
    sleep(pace.delay());
    continue;
  }

  blind = 0;

  // The one signal no wording can argue with: if the number moved, the reading is working, whatever
  // the journal looked like from in here.
  if (value !== lastValue) {
    lastValue = value;
    reads += unreadPending;
    unreadPending = 0;
    unreadSaid = false;
    stall.progressed();
  }

  if (value >= GOAL) {
    stop = `${skill.name()} is at ${tenths(value)}`;
    break;
  }

  const outcome = evaluateOnce();

  if (outcome !== 'throttled') {
    throttled = 0;
  }

  switch (outcome) {
    // Both rolled the skill, which is the whole of the training: a check that fails still asked the
    // shard for one
    case 'evaluated':
    case 'missed':
      reads++;
      unreadSaid = false;
      pace.landed();
      stall.progressed();

      if (outcome === 'missed') {
        missed++;
      }
      break;

    case 'saving':
      waitOutSave();
      throttled = 0;
      stall.progressed();
      break;

    // The shard's own skill timer, which nothing in the API reports. The pace is raised as well as
    // backed off from, or the next cycle walks straight back into it.
    case 'throttled':
      throttled++;
      log(`evalint: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the read';
      }
      break;

    default: {
      const terminal = STOP_REASON[outcome];

      if (terminal) {
        stop = terminal;
        break;
      }

      unread++;
      unreadPending++;

      if (!unreadSaid) {
        unreadSaid = true;
        log('evalint: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls');
      }
    }
  }

  if (reads >= reported + LOG_EVERY) {
    reported = reads;
    log(
      `evalint: ${reads} reads, ${missed} of them missed, ` +
        `${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`,
    );
  }

  stall.endCycle(outcome, cycle, reads);
  stop = stop ?? stall.reason();
  sleep(pace.delay());
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
const ended = skill.value();

log(
  `evalint: ${reads} reads, ${missed} missed, ${skill.name()} ${tenths(start)} -> ` +
    `${ended === undefined ? 'unknown' : tenths(ended)}`,
);

// Said only when there were any, and said last so it reads as the footnote it is
if (unread > 0) {
  log(`evalint: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
}

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended must not be the line that gets away
log(`evalint: stopping - ${reason}`);
exit(`evalint: ${reason}`);
