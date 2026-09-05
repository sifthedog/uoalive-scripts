import { die } from '../lib/die.js';
import { hex, isMobile } from '../lib/entity.js';
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { createPace } from '../lib/pace.js';
import { pickOne } from '../lib/pick.js';
import { createSkillReader, tenths } from '../lib/skill.js';
import {
  GOAL,
  LOG_EVERY,
  MAX_AWAY,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_THROTTLED,
  OPL_TIMEOUT,
  PACE_EASE_AFTER,
  PACE_MAX,
  PACE_STEP,
  READ_DELAY,
  SKILL_POLL,
  SKILL_TIMEOUT,
  STALL_STOP,
  STALL_WARN,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { closeStrayGump } from './gump.js';
import { stopReason } from './guards.js';
import { beat, heartbeat } from './heartbeat.js';
import { loreOnce, STOP_REASON } from './lore.js';
import { isSaving, waitOutSave } from './save.js';

const picked =
  pickOne({
    prefix: 'lore',
    prompt: 'target the creature to read',
    oplTimeout: OPL_TIMEOUT,
  }) ?? die('lore: nothing picked');

// The serial is resolved once and read every cycle: a pet that has been stabled, killed or led away
// is the ordinary way an overnight run ends, and walking at a serial the client no longer knows is
// how it would otherwise end silently.
const animal = client.findObject(picked.serial);

if (!animal || !isMobile(animal)) {
  die(`lore: ${hex(picked.serial)} is not a creature`);
}

const skill = createSkillReader({
  skill: Skills.AnimalLore,
  label: 'Animal Lore',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

const start = skill.waitForSkill() ?? die('lore: the client is not reporting the skill');

log(`lore: reading '${picked.name || hex(picked.serial)}' - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}`);

// Said rather than corrected: a power scroll may be on its way, and a run that quietly retargeted
// itself would be lying about its goal.
const cap = skill.cap();

if (cap !== undefined && GOAL > cap) {
  log(`lore: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
}

const pace = createPace({
  floor: READ_DELAY,
  step: PACE_STEP,
  max: PACE_MAX,
  easeAfter: PACE_EASE_AFTER,
});

const stall = createStallWatch({
  prefix: 'lore',
  without: 'cycles without a read',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

let reads = 0;
let missed = 0;
let throttled = 0;
let away = 0;
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

  if (!client.findObject(picked.serial)) {
    stop = `'${picked.name || hex(picked.serial)}' is gone`;
    break;
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

  const outcome = loreOnce(picked.serial);

  if (outcome !== 'throttled') {
    throttled = 0;
  }

  if (outcome !== 'tooFar') {
    away = 0;
  }

  switch (outcome) {
    // Both rolled the skill, which is the whole of the training: a lore that fails its check still
    // asked the shard for one
    case 'lored':
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
      log(`lore: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the read';
      }
      break;

    // A pet wanders off and wanders back, so this waits rather than stopping
    case 'tooFar':
      away++;
      log(`lore: out of range (${away}/${MAX_AWAY}) - walk back to it`);

      if (away >= MAX_AWAY) {
        stop = 'the creature stayed out of range';
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
        log('lore: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls');
      }
    }
  }

  if (reads >= reported + LOG_EVERY) {
    reported = reads;
    log(
      `lore: ${reads} reads, ${missed} of them missed, ` +
        `${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`,
    );
  }

  stall.endCycle(outcome, cycle, reads);
  stop = stop ?? stall.reason();
  sleep(pace.delay());
}

// A read that was refused partway through can leave one on screen, and a run that ends with the pet
// window open is the thing you notice before the log line
closeStrayGump();

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
const ended = skill.value();

log(
  `lore: ${reads} reads, ${missed} missed, ${skill.name()} ${tenths(start)} -> ` +
    `${ended === undefined ? 'unknown' : tenths(ended)}`,
);

// Said only when there were any, and said last so it reads as the footnote it is
if (unread > 0) {
  log(`lore: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
}

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended must not be the line that gets away
log(`lore: stopping - ${reason}`);
exit(`lore: ${reason}`);
