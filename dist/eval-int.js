"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap2) => Math.min(step * count, cap2);
  var createStallWatch = (options) => {
    let since = 0;
    let reason2;
    return {
      endCycle: (phase, cycle, tally) => {
        options.heartbeat.beat(phase, cycle, tally);
        since++;
        if (since === options.warnAt) {
          log(`${options.prefix}: ${options.warnAt} ${options.without}, last was '${phase}'`);
        }
        if (since >= options.stopAt) {
          reason2 = `no progress in ${options.stopAt} cycles, last was '${phase}'`;
        }
      },
      progressed: () => {
        since = 0;
      },
      reason: () => reason2
    };
  };

  // src/lib/pace.ts
  var createPace = (options) => {
    let delay = options.floor;
    let landed = 0;
    return {
      delay: () => delay,
      refused: () => {
        landed = 0;
        delay = Math.min(delay + options.step, options.max);
        return delay;
      },
      landed: () => {
        if (++landed < options.easeAfter) {
          return delay;
        }
        landed = 0;
        delay = Math.max(options.floor, delay - options.step);
        return delay;
      }
    };
  };

  // src/lib/skill.ts
  var tenths = (value) => (value / 10).toFixed(1);
  var createSkillReader = ({
    skill: skill2,
    label,
    timeoutMs,
    pollMs
  }) => {
    const value = () => player.getSkill(skill2)?.value;
    return {
      value,
      cap: () => player.getSkill(skill2)?.cap,
      name: () => player.getSkill(skill2)?.name ?? label,
      // The skill list arrives asynchronously, so a run that read it once would decide what to train
      // from whatever the client happened to know at paste time.
      waitForSkill: () => {
        for (let waited = 0; waited < timeoutMs; waited += pollMs) {
          const reading = value();
          if (reading !== void 0) {
            return reading;
          }
          sleep(pollMs);
        }
        return value();
      }
    };
  };

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var LOG_EVERY = 25;
  var SAVE_WAIT = 6e4;
  var SAVE_POLL = 1e3;
  var SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"];
  var SAVING_TEXT = ["The world is saving", "Saving world", "World save started"];
  var THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait"
  ];
  var UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill"
  ];
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

  // src/evalint/config.ts
  var GOAL = 1e3;
  var USE_DELAY = 1e3;
  var PACE_STEP = 400;
  var PACE_MAX = 8e3;
  var PACE_EASE_AFTER = 5;
  var EVAL_TIMEOUT = 1e3;
  var SKILL_TIMEOUT = 5e3;
  var SKILL_POLL = 250;
  var MAX_BLIND_READS = 20;
  var STALL_WARN = 100;
  var STALL_STOP = 1e3;
  var OUTCOME_TEXT = {
    // A failed check rolls the skill too, so these are half of what the training is made of
    missed: [
      "You cannot judge their mental abilities",
      "You have no idea of their mental abilities",
      "You cannot judge that creature"
    ],
    // Stems the whole ladder shares rather than its rungs. Not 'mental', which the misses carry.
    evaluated: ["intellect", "mind"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/evalint/evaluate.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var STOP_REASON = {
    unskilled: "the shard says this character cannot evaluate intelligence"
  };
  var evaluateOnce = () => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    journal.clear();
    player.useSkill(Skills.EvalInt, player.serial);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, EVAL_TIMEOUT);
    return matched ? outcomeFor(matched) ?? "unknown" : "unknown";
  };

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var firstReason = (...guards) => {
    for (const guard of guards) {
      const reason2 = guard();
      if (reason2) {
        return reason2;
      }
    }
    return void 0;
  };

  // src/evalint/guards.ts
  var stopReason = () => firstReason(dead);

  // src/lib/heartbeat.ts
  var createHeartbeat = (options) => {
    let lastBeat;
    return {
      beat: (phase, cycle, tally) => {
        const time = now();
        if (lastBeat === void 0) {
          lastBeat = time;
          return;
        }
        if (time - lastBeat < options.everyMs) {
          return;
        }
        lastBeat = time;
        log(
          `${options.prefix}: still here - ${phase}, cycle ${cycle}, at ${player.x},${player.y}, ${player.weight}/${player.weightMax}, ${tally} ${options.noun}`
        );
      },
      // For the paths that report on their own cadence, so the next beat is a full interval after they
      // stop rather than immediately on top of their last line
      resetBeat: () => {
        lastBeat = now();
      }
    };
  };

  // src/evalint/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "evalint",
    noun: "reads",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/save.ts
  var createSaveWatch = (options) => ({
    isSaving: () => options.savingText.some((text) => journal.containsText(text)),
    waitOutSave: () => {
      log("save: the world is saving, waiting it out");
      const said = (texts) => texts.some((text) => journal.containsText(text));
      let ended2 = said(options.doneText) ? "the shard had already finished" : void 0;
      journal.clear();
      for (let waited = 0; !ended2 && waited < options.waitMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (said(options.doneText)) {
          ended2 = "the shard says it is done";
        } else if (options.stopReason()) {
          ended2 = "the run has a reason to stop";
        }
      }
      log(`save: ${ended2 ?? `nothing said in ${Math.round(options.waitMs / 1e3)}s`}, carrying on`);
      options.onDone();
    }
  });

  // src/evalint/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/evalint/index.ts
  var skill = createSkillReader({
    skill: Skills.EvalInt,
    label: "Evaluating Intelligence",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var start = skill.waitForSkill() ?? die("evalint: the client is not reporting the skill");
  log(`evalint: reading yourself - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}`);
  var cap = skill.cap();
  if (cap !== void 0 && GOAL > cap) {
    log(`evalint: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
  }
  var pace = createPace({ floor: USE_DELAY, step: PACE_STEP, max: PACE_MAX, easeAfter: PACE_EASE_AFTER });
  var stall = createStallWatch({
    prefix: "evalint",
    without: "cycles without a read",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  var reads = 0;
  var missed = 0;
  var throttled = 0;
  var blind = 0;
  var reported = 0;
  var lastValue = start;
  var stop;
  var unread = 0;
  var unreadPending = 0;
  var unreadSaid = false;
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (isSaving()) {
      waitOutSave();
      throttled = 0;
      unreadSaid = false;
      stall.progressed();
      stall.endCycle("saving", cycle, reads);
      continue;
    }
    const value = skill.value();
    if (value === void 0) {
      blind++;
      if (blind >= MAX_BLIND_READS) {
        stop = "the client stopped reporting the skill";
        break;
      }
      beat("unreadable skill", cycle, reads);
      sleep(pace.delay());
      continue;
    }
    blind = 0;
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
    if (outcome !== "throttled") {
      throttled = 0;
    }
    switch (outcome) {
      // Both rolled the skill, which is the whole of the training: a check that fails still asked the
      // shard for one
      case "evaluated":
      case "missed":
        reads++;
        unreadSaid = false;
        pace.landed();
        stall.progressed();
        if (outcome === "missed") {
          missed++;
        }
        break;
      case "saving":
        waitOutSave();
        throttled = 0;
        stall.progressed();
        break;
      // The shard's own skill timer, which nothing in the API reports. The pace is raised as well as
      // backed off from, or the next cycle walks straight back into it.
      case "throttled":
        throttled++;
        log(`evalint: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the read";
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
          log("evalint: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls");
        }
      }
    }
    if (reads >= reported + LOG_EVERY) {
      reported = reads;
      log(
        `evalint: ${reads} reads, ${missed} of them missed, ${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`
      );
    }
    stall.endCycle(outcome, cycle, reads);
    stop = stop ?? stall.reason();
    sleep(pace.delay());
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  var ended = skill.value();
  log(
    `evalint: ${reads} reads, ${missed} missed, ${skill.name()} ${tenths(start)} -> ${ended === void 0 ? "unknown" : tenths(ended)}`
  );
  if (unread > 0) {
    log(`evalint: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
  }
  log(`evalint: stopping - ${reason}`);
  exit(`evalint: ${reason}`);
})();
