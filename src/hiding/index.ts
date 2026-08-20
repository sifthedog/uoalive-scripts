import { die } from '../lib/die.js';
import { createStallWatch } from '../lib/loop.js';
import { createSkillReader, type SkillReader, tenths } from '../lib/skill.js';
import {
  ATTEMPT_DELAY,
  HIDING_GOAL,
  LOG_EVERY,
  MAX_BLIND_READS,
  MAX_CYCLES,
  SKILL_POLL,
  SKILL_TIMEOUT,
  STALL_STOP,
  STALL_WARN,
  STEALTH_GOAL,
} from './config.js';
import { stopReason } from './guards.js';
import { hideOnce } from './hide.js';
import { beat, heartbeat } from './heartbeat.js';
import { isSaving, waitOutSave } from './save.js';
import { stealthOnce } from './stealth.js';

const hiding = createSkillReader({
  skill: Skills.Hiding,
  label: 'Hiding',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const stealth = createSkillReader({
  skill: Skills.Stealth,
  label: 'Stealth',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const startHiding = hiding.waitForSkill() ?? die('hiding: the client is not reporting Hiding');
const startStealth = stealth.waitForSkill() ?? die('hiding: the client is not reporting Stealth');

const shown = (value: number | undefined): string => (value === undefined ? 'unknown' : tenths(value));

log(
  `hiding: ${hiding.name()} at ${tenths(startHiding)}/${tenths(HIDING_GOAL)}, ` +
    `${stealth.name()} at ${tenths(startStealth)}/${tenths(STEALTH_GOAL)}`,
);

// Said rather than corrected: a power scroll may be on its way, and a run that quietly retargeted
// itself would be lying about its goal.
const sayCap = (reader: SkillReader, goal: number): void => {
  const cap = reader.cap();

  if (cap !== undefined && goal > cap) {
    log(`hiding: the shard caps ${reader.name()} at ${tenths(cap)} - it will not reach ${tenths(goal)}`);
  }
};

sayCap(hiding, HIDING_GOAL);
sayCap(stealth, STEALTH_GOAL);

const stall = createStallWatch({
  prefix: 'hiding',
  without: 'cycles without an attempt',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

let hides = 0;
let stealths = 0;
let attempts = 0;
let blind = 0;
let reported = 0;

// What the run believes, because a client that does not publish isHidden would hide forever and
// never stealth. The flag going up is trusted; it being down is not.
let believed = false;

let lastHiding = startHiding;
let lastStealth = startStealth;
let stop: string | undefined;

// Reported at the end so a wrong phrase table is still obvious, but never a reason to stop: whether
// the run is getting anywhere is a separate question from whether it can follow along.
let unread = 0;

// The ones since a skill last moved, credited to the tally when one does
let unreadPending = 0;

// Said once per stretch rather than once per attempt, so a real ending does not scroll away
let unreadSaid = false;

const unreadable = (): void => {
  unread++;
  unreadPending++;

  if (!unreadSaid) {
    unreadSaid = true;
    log('hiding: outcome unreadable - carrying on; check HIDE_TEXT and STEALTH_TEXT if this run stalls');
  }
};

const landed = (): void => {
  attempts++;
  unreadSaid = false;
  stall.progressed();
};

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();

  if (stop) {
    break;
  }

  if (isSaving()) {
    waitOutSave();
    unreadSaid = false;
    stall.progressed();
    stall.endCycle('saving', cycle, attempts);
    continue;
  }

  const hidingValue = hiding.value();
  const stealthValue = stealth.value();

  // Never read as 0, which would be a real skill value and would hide a character who is already done
  if (hidingValue === undefined || stealthValue === undefined) {
    blind++;

    if (blind >= MAX_BLIND_READS) {
      stop = 'the client stopped reporting the skills';
      break;
    }

    beat('unreadable skill', cycle, attempts);
    sleep(ATTEMPT_DELAY);
    continue;
  }

  blind = 0;

  // The one signal no wording can argue with: if either number moved, the training is working,
  // whatever the journal looked like from in here.
  if (hidingValue !== lastHiding || stealthValue !== lastStealth) {
    lastHiding = hidingValue;
    lastStealth = stealthValue;
    attempts += unreadPending;
    unreadPending = 0;
    unreadSaid = false;
    stall.progressed();
  }

  if (hidingValue >= HIDING_GOAL && stealthValue >= STEALTH_GOAL) {
    stop = `${hiding.name()} at ${tenths(hidingValue)} and ${stealth.name()} at ${tenths(stealthValue)}`;
    break;
  }

  let label: string;

  if (!(believed || player.isHidden)) {
    const outcome = hideOnce();

    label = `hide:${outcome}`;

    switch (outcome) {
      // Both rolled the skill, which is the whole of the training
      case 'hidden':
      case 'failed':
        hides++;
        believed = outcome === 'hidden';
        landed();
        break;

      case 'saving':
        waitOutSave();
        unreadSaid = false;
        stall.progressed();
        break;

      // Neither rolled the skill, and at this cadence a refusal is the shard's usual answer
      case 'busy':
      case 'throttled':
        break;

      default:
        believed = player.isHidden;
        unreadable();
    }
  } else {
    const outcome = stealthOnce();

    label = `stealth:${outcome}`;

    switch (outcome) {
      case 'quietly':
        stealths++;
        landed();
        break;

      // Rolled the skill and revealed us, so the next cycle hides again
      case 'failed':
        stealths++;
        believed = false;
        landed();
        break;

      // The shard disagrees with the flag, or wants more Hiding than we have. Hiding again answers
      // both, and rolls the skill that clears the gate.
      case 'notHidden':
      case 'notHiddenWell':
        believed = false;
        break;

      case 'armour':
        stop = 'the shard will not stealth in this armour - take it off and run again';
        break;

      case 'saving':
        waitOutSave();
        unreadSaid = false;
        stall.progressed();
        break;

      case 'throttled':
        break;

      default:
        unreadable();
    }
  }

  if (attempts >= reported + LOG_EVERY) {
    reported = attempts;
    log(
      `hiding: ${hides} hides, ${stealths} stealth uses, ` +
        `${hiding.name()} at ${tenths(hidingValue)}/${tenths(HIDING_GOAL)}, ` +
        `${stealth.name()} at ${tenths(stealthValue)}/${tenths(STEALTH_GOAL)}`,
    );
  }

  stall.endCycle(label, cycle, attempts);
  stop = stop ?? stall.reason();
  sleep(ATTEMPT_DELAY);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;

log(
  `hiding: ${hides} hides, ${stealths} stealth uses, ` +
    `${hiding.name()} ${tenths(startHiding)} -> ${shown(hiding.value())}, ` +
    `${stealth.name()} ${tenths(startStealth)} -> ${shown(stealth.value())}`,
);

// Said only when there were any, and said last so it reads as the footnote it is
if (unread > 0) {
  log(`hiding: ${unread} outcome(s) went unread - add the shard's wording to HIDE_TEXT or STEALTH_TEXT`);
}

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended must not be the line that gets away
log(`hiding: stopping - ${reason}`);
exit(`hiding: ${reason}`);
