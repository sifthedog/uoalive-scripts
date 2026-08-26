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

  // src/lib/skill.ts
  var tenths = (value) => (value / 10).toFixed(1);
  var createSkillReader = ({
    skill,
    label,
    timeoutMs,
    pollMs
  }) => {
    const value = () => player.getSkill(skill)?.value;
    return {
      value,
      cap: () => player.getSkill(skill)?.cap,
      name: () => player.getSkill(skill)?.name ?? label,
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
  var HEARTBEAT_EVERY = 3e4;
  var STALL_WARN = 60;
  var STALL_STOP = 300;
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

  // src/hiding/config.ts
  var HIDING_GOAL = 1e3;
  var STEALTH_GOAL = 1e3;
  var ATTEMPT_DELAY = 500;
  var HIDE_TIMEOUT = 500;
  var STEALTH_TIMEOUT = 500;
  var MAX_CYCLES = 5e4;
  var SKILL_TIMEOUT = 5e3;
  var SKILL_POLL = 250;
  var MAX_BLIND_READS = 20;
  var HIDE_TEXT = {
    hidden: ["You have hidden yourself well"],
    // Most of what training is made of: a refused hide rolls the skill exactly as a successful one does
    failed: ["You can't seem to hide here", "You cannot seem to hide here"],
    busy: ["You are busy doing something else and cannot hide"],
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };
  var STEALTH_TEXT = {
    quietly: ["You begin to move quietly"],
    // Rolls the skill and reveals you, which is the signal to hide again
    failed: ["You fail in your attempt to move unnoticed"],
    notHidden: ["You must hide first"],
    // Before the bare wordings UNSKILLED_TEXT ends with, since outcomeFor takes the first bucket that matches
    notHiddenWell: ["You are not hidden well enough", ...UNSKILLED_TEXT],
    armour: ["You could not hide unless you were wearing lighter armor"],
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
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

  // src/hiding/guards.ts
  var stopReason = () => firstReason(dead);

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/hiding/hide.ts
  var { all: ALL_HIDE_TEXT, outcomeFor } = outcomeVocabulary(HIDE_TEXT);
  var hideOnce = () => {
    const before = player.isHidden;
    journal.clear();
    player.useSkill(Skills.Hiding);
    const matched = journal.waitForTextAny(ALL_HIDE_TEXT, void 0, HIDE_TIMEOUT);
    if (matched) {
      return outcomeFor(matched) ?? "unknown";
    }
    return !before && player.isHidden ? "hidden" : "unknown";
  };

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

  // src/hiding/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "hiding",
    noun: "attempts",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/save.ts
  var createSaveWatch = (options) => ({
    isSaving: () => options.savingText.some((text) => journal.containsText(text)),
    waitOutSave: () => {
      log("save: the world is saving, waiting it out");
      const said = (texts) => texts.some((text) => journal.containsText(text));
      let ended = said(options.doneText) ? "the shard had already finished" : void 0;
      journal.clear();
      for (let waited = 0; !ended && waited < options.waitMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (said(options.doneText)) {
          ended = "the shard says it is done";
        } else if (options.stopReason()) {
          ended = "the run has a reason to stop";
        }
      }
      log(`save: ${ended ?? `nothing said in ${Math.round(options.waitMs / 1e3)}s`}, carrying on`);
      options.onDone();
    }
  });

  // src/hiding/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/hiding/stealth.ts
  var { all: ALL_STEALTH_TEXT, outcomeFor: outcomeFor2 } = outcomeVocabulary(STEALTH_TEXT);
  var stealthOnce = () => {
    const before = player.isHidden;
    journal.clear();
    player.useSkill(Skills.Stealth);
    const matched = journal.waitForTextAny(ALL_STEALTH_TEXT, void 0, STEALTH_TIMEOUT);
    if (matched) {
      return outcomeFor2(matched) ?? "unknown";
    }
    return before && !player.isHidden ? "failed" : "unknown";
  };

  // src/hiding/index.ts
  var hiding = createSkillReader({
    skill: Skills.Hiding,
    label: "Hiding",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var stealth = createSkillReader({
    skill: Skills.Stealth,
    label: "Stealth",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var startHiding = hiding.waitForSkill() ?? die("hiding: the client is not reporting Hiding");
  var startStealth = stealth.waitForSkill() ?? die("hiding: the client is not reporting Stealth");
  var shown = (value) => value === void 0 ? "unknown" : tenths(value);
  log(
    `hiding: ${hiding.name()} at ${tenths(startHiding)}/${tenths(HIDING_GOAL)}, ${stealth.name()} at ${tenths(startStealth)}/${tenths(STEALTH_GOAL)}`
  );
  var sayCap = (reader, goal) => {
    const cap = reader.cap();
    if (cap !== void 0 && goal > cap) {
      log(`hiding: the shard caps ${reader.name()} at ${tenths(cap)} - it will not reach ${tenths(goal)}`);
    }
  };
  sayCap(hiding, HIDING_GOAL);
  sayCap(stealth, STEALTH_GOAL);
  var stall = createStallWatch({
    prefix: "hiding",
    without: "cycles without an attempt",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  var hides = 0;
  var stealths = 0;
  var attempts = 0;
  var blind = 0;
  var reported = 0;
  var believed = false;
  var lastHiding = startHiding;
  var lastStealth = startStealth;
  var stop;
  var unread = 0;
  var unreadPending = 0;
  var unreadSaid = false;
  var unreadable = () => {
    unread++;
    unreadPending++;
    if (!unreadSaid) {
      unreadSaid = true;
      log("hiding: outcome unreadable - carrying on; check HIDE_TEXT and STEALTH_TEXT if this run stalls");
    }
  };
  var landed = () => {
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
      stall.endCycle("saving", cycle, attempts);
      continue;
    }
    const hidingValue = hiding.value();
    const stealthValue = stealth.value();
    if (hidingValue === void 0 || stealthValue === void 0) {
      blind++;
      if (blind >= MAX_BLIND_READS) {
        stop = "the client stopped reporting the skills";
        break;
      }
      beat("unreadable skill", cycle, attempts);
      sleep(ATTEMPT_DELAY);
      continue;
    }
    blind = 0;
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
    let label;
    if (!(believed || player.isHidden)) {
      const outcome = hideOnce();
      label = `hide:${outcome}`;
      switch (outcome) {
        // Both rolled the skill, which is the whole of the training
        case "hidden":
        case "failed":
          hides++;
          believed = outcome === "hidden";
          landed();
          break;
        case "saving":
          waitOutSave();
          unreadSaid = false;
          stall.progressed();
          break;
        // Neither rolled the skill, and at this cadence a refusal is the shard's usual answer
        case "busy":
        case "throttled":
          break;
        default:
          believed = player.isHidden;
          unreadable();
      }
    } else {
      const outcome = stealthOnce();
      label = `stealth:${outcome}`;
      switch (outcome) {
        case "quietly":
          stealths++;
          landed();
          break;
        // Rolled the skill and revealed us, so the next cycle hides again
        case "failed":
          stealths++;
          believed = false;
          landed();
          break;
        // The shard disagrees with the flag, or wants more Hiding than we have. Hiding again answers
        // both, and rolls the skill that clears the gate.
        case "notHidden":
        case "notHiddenWell":
          believed = false;
          break;
        case "armour":
          stop = "the shard will not stealth in this armour - take it off and run again";
          break;
        case "saving":
          waitOutSave();
          unreadSaid = false;
          stall.progressed();
          break;
        case "throttled":
          break;
        default:
          unreadable();
      }
    }
    if (attempts >= reported + LOG_EVERY) {
      reported = attempts;
      log(
        `hiding: ${hides} hides, ${stealths} stealth uses, ${hiding.name()} at ${tenths(hidingValue)}/${tenths(HIDING_GOAL)}, ${stealth.name()} at ${tenths(stealthValue)}/${tenths(STEALTH_GOAL)}`
      );
    }
    stall.endCycle(label, cycle, attempts);
    stop = stop ?? stall.reason();
    sleep(ATTEMPT_DELAY);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(
    `hiding: ${hides} hides, ${stealths} stealth uses, ${hiding.name()} ${tenths(startHiding)} -> ${shown(hiding.value())}, ${stealth.name()} ${tenths(startStealth)} -> ${shown(stealth.value())}`
  );
  if (unread > 0) {
    log(`hiding: ${unread} outcome(s) went unread - add the shard's wording to HIDE_TEXT or STEALTH_TEXT`);
  }
  log(`hiding: stopping - ${reason}`);
  exit(`hiding: ${reason}`);
})();
