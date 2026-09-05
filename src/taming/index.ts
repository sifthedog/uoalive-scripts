import { die } from '../lib/die.js';
import { distanceTo, hex, isMobile, nameOf } from '../lib/entity.js';
import { backoffFor, createStallWatch } from '../lib/loop.js';
import { createPace } from '../lib/pace.js';
import { pickOne } from '../lib/pick.js';
import { createSkillReader, tenths } from '../lib/skill.js';
import {
  AFTER_TAME,
  ANGRY_DELAY,
  LOG_EVERY,
  MAX_ANGRY,
  MAX_AWAY,
  MAX_CONTESTED,
  MAX_CYCLES,
  MAX_PENDING,
  MAX_THROTTLED,
  OPL_TIMEOUT,
  PACE_EASE_AFTER,
  PACE_MAX,
  PACE_STEP,
  PET_NAME,
  SKILL_POLL,
  SKILL_TIMEOUT,
  STALL_STOP,
  STALL_WARN,
  TAME_DELAY,
  TAME_RANGE,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { leaveOut, nextQuarry } from './hunt.js';
import { beat, heartbeat } from './heartbeat.js';
import { commandKill, releasePet, renamePet } from './pet.js';
import { isSaving, waitOutSave } from './save.js';
import { STOP_REASON, tameOnce } from './tame.js';
import { keepUp, walkTo } from './walk.js';

const skill = createSkillReader({
  skill: Skills.AnimalTaming,
  label: 'Animal Taming',
  timeoutMs: SKILL_TIMEOUT,
  pollMs: SKILL_POLL,
});

// Not died on, unlike the trainers: the goal here is a sentence rather than a number, so a client
// that will not report the skill costs a log line and nothing else
const start = skill.waitForSkill();

const reading = (value: number | undefined): string =>
  value === undefined ? 'unknown' : tenths(value);

const pace = createPace({
  floor: TAME_DELAY,
  step: PACE_STEP,
  max: PACE_MAX,
  easeAfter: PACE_EASE_AFTER,
});

const stall = createStallWatch({
  prefix: 'tame',
  without: 'cycles without an attempt',
  warnAt: STALL_WARN,
  stopAt: STALL_STOP,
  heartbeat,
});

log(`tame: ${skill.name()} at ${reading(start)}`);

let tamed = 0;
let attempts = 0;
let lastValue = start;
let failures = 0;
let reported = 0;
let stop: string | undefined;

// Reported at the end so a wrong OUTCOME_TEXT is still obvious, but never a reason to stop
let unread = 0;
let unnamed = 0;
let unfinished = 0;

// Said once per stretch rather than once per cycle, so a real ending does not scroll away
let unreadSaid = false;

// Renamed before anything else is done with it: once it is not your pet the Rename entry is gone
// from its menu
const afterTame = (serial: number, name: string): void => {
  let called = name;

  if (PET_NAME) {
    const renamed = renamePet(serial, PET_NAME);

    if (renamed === 'renamed') {
      called = PET_NAME;
      log(`tame: renamed '${name}' to '${PET_NAME}'`);
    } else {
      unnamed++;
      log(`tame: could not rename '${name}' (${renamed}) - carrying on`);
    }
  }

  if (AFTER_TAME === 'kill') {
    const ordered = commandKill(serial, called);

    if (ordered !== 'ordered') {
      unfinished++;
      log(`tame: could not order '${called}' to kill (${ordered}) - carrying on`);
    }

    return;
  }

  if (AFTER_TAME !== 'release') {
    return;
  }

  const released = releasePet(serial);

  if (released === 'released') {
    log(`tame: released '${called}'`);
  } else {
    unfinished++;
    log(`tame: could not release '${called}' (${released}) - carrying on`);
  }
};

// The graphic the last hand-picked animal set, and so what the hunt looks for
let hunting: number | undefined;

while (!stop) {
  const sighted = hunting === undefined ? undefined : nextQuarry(hunting);
  let quarry = sighted?.quarry;

  // Asked for only when there is nothing of that type left in sight
  if (!quarry) {
    const picked = pickOne({
      prefix: 'tame',
      prompt: 'target the creature to tame',
      oplTimeout: OPL_TIMEOUT,
    });

    // The only sign the client gives that ESC was pressed. On the first pick there is nothing to
    // show for the run, so it reads as a mistake rather than as closing the session.
    if (!picked) {
      stop = tamed > 0 ? `${tamed} tamed` : 'nothing picked';
      break;
    }

    const animal = client.findObject(picked.serial);

    // A bad pick puts the cursor back up rather than ending the session
    if (!animal || !isMobile(animal)) {
      log(`tame: ${hex(picked.serial)} is not a creature`);
      continue;
    }

    // Left unset by a pick the client has no art for, so the run goes on asking rather than hunting
    // for a graphic that matches nothing
    hunting = picked.graphic || animal.graphic || undefined;

    quarry = { serial: picked.serial, name: nameOf(picked), graphic: hunting ?? 0 };
  }

  const name = quarry.name;
  const others = (sighted?.inSight ?? 1) - 1;

  log(`tame: taming '${name}'${others > 0 ? ` (${others} more in sight)` : ''}`);

  let done: string | undefined;
  let accepted = false;
  let throttled = 0;
  let away = 0;
  let contested = 0;
  let angry = 0;
  let pending = 0;

  for (let cycle = 0; cycle < MAX_CYCLES && !stop && !done; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }

    // Before anything else: during a save every attempt is refused, and each refusal would be
    // charged to a counter that ends the run
    if (isSaving()) {
      waitOutSave();
      throttled = 0;
      stall.progressed();
      stall.endCycle('saving', cycle, attempts);
      continue;
    }

    const found = client.findObject(quarry.serial);

    if (!found || !isMobile(found)) {
      done = `'${name}' is gone`;
      break;
    }

    if (distanceTo(found) > TAME_RANGE) {
      // Ground made up is reason enough for another cycle: an animal that keeps walking off is
      // chased for as long as the gap is closing, and only a chase that gains nothing counts
      if (walkTo(quarry.serial) !== 'stuck') {
        away = 0;
      } else if (++away >= MAX_AWAY) {
        done = `could not get near '${name}'`;
        break;
      }

      beat('walking', cycle, attempts);
      stall.endCycle('walking', cycle, attempts);

      // Read here as well as after the switch, or a chase that never lands an attempt is bounded by
      // nothing but MAX_CYCLES
      stop = stop ?? stall.reason();
      continue;
    }

    const value = skill.value();

    // The one signal no wording can argue with: if the number moved, the taming is working, whatever
    // the journal looked like from in here
    if (value !== undefined && value !== lastValue) {
      lastValue = value;
      unreadSaid = false;
      stall.progressed();
    }

    // The attempt blocks for as long as the shard takes to answer, and the animal walks the whole
    // time, so the chase carries on between the slices of that wait
    const outcome = tameOnce(quarry.serial, () => keepUp(quarry.serial));

    if (outcome !== 'throttled') {
      throttled = 0;
    }

    if (outcome !== 'tooFar') {
      away = 0;
    }

    if (outcome !== 'contested') {
      contested = 0;
    }

    if (outcome !== 'angry') {
      angry = 0;
    }

    if (outcome !== 'pending') {
      pending = 0;
    }

    switch (outcome) {
      case 'tamed':
        attempts++;
        tamed++;
        stall.progressed();
        accepted = true;
        done = `'${name}' accepted you as master`;
        break;

      // A failed tame still rolled the skill, which is the ordinary cycle rather than a refusal
      case 'failed':
        attempts++;
        failures++;
        unreadSaid = false;
        pace.landed();
        stall.progressed();
        break;

      // The shard took the attempt and never answered. Raise TAME_RESOLVE_TIMEOUT if this run ends
      // here.
      case 'pending':
        attempts++;
        pending++;

        if (pending >= MAX_PENDING) {
          stop = 'attempts kept starting and never resolving';
        }
        break;

      case 'angry':
        angry++;
        log(`tame: '${name}' is too angry (${angry}/${MAX_ANGRY}), letting it settle`);
        sleep(ANGRY_DELAY);

        if (angry >= MAX_ANGRY) {
          done = `'${name}' stayed too angry to tame`;
        }
        break;

      case 'contested':
        contested++;
        log(`tame: someone else has '${name}' (${contested}/${MAX_CONTESTED})`);

        if (contested >= MAX_CONTESTED) {
          done = `another tamer has '${name}'`;
        }
        break;

      // Walked at rather than waited out, so a creature that bolted mid-attempt is chased
      case 'tooFar':
        if (walkTo(quarry.serial) !== 'stuck') {
          away = 0;
        } else if (++away >= MAX_AWAY) {
          done = `could not get near '${name}'`;
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
        log(`tame: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

        if (throttled >= MAX_THROTTLED) {
          stop = 'the shard kept refusing the attempt';
        }
        break;

      default: {
        const terminal = STOP_REASON[outcome];

        if (terminal) {
          done = terminal;
          break;
        }

        unread++;

        if (!unreadSaid) {
          unreadSaid = true;
          log('tame: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls');
        }
      }
    }

    if (attempts >= reported + LOG_EVERY) {
      reported = attempts;
      log(`tame: ${attempts} attempts, ${failures} failed, ${skill.name()} at ${reading(value)}`);
    }

    stall.endCycle(outcome, cycle, attempts);
    stop = stop ?? stall.reason();
    sleep(pace.delay());
  }

  // Only about this animal: a session-ending fault is reported by the closing lines instead
  if (done) {
    log(`tame: ${done}`);
  } else if (!stop) {
    log(`tame: hit the ${MAX_CYCLES} cycle backstop on '${name}'`);
  }

  // After the line that says it was tamed, and even when the session is stopping: whatever is done
  // with the animal is not worth skipping because the run happens to be ending
  if (accepted) {
    afterTame(quarry.serial, name);
  }

  // Every ending, not just the ones that gave up: an animal this run is finished with must not be
  // the one the next scan picks straight back up
  leaveOut(quarry.serial);
}

const reason = stop ?? 'the session ended';

log(
  `tame: ${tamed} tamed over ${attempts} attempts, ${failures} failed, ` +
    `${skill.name()} ${reading(start)} -> ${reading(skill.value())}`,
);

// Said only when there were any, and said last so it reads as the footnote it is
if (unread > 0) {
  log(`tame: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
}

if (unnamed > 0 || unfinished > 0) {
  log(
    `tame: ${unnamed} rename(s) and ${unfinished} ${AFTER_TAME} order(s) did not go through - ` +
      'check the menu wordings in config against the menu the shard sends',
  );
}

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended must not be the line that gets away
log(`tame: stopping - ${reason}`);
exit(`tame: ${reason}`);
