"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var isMobile = (entity) => entity._tag === "Mobile";

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

  // src/lib/opl.ts
  var threw = false;
  var queryOPL = (serial, timeoutMs, prefix) => {
    try {
      return client.queryItemOPL(serial, timeoutMs);
    } catch (error) {
      if (!threw) {
        threw = true;
        log(`${prefix}: the tooltip lookup would not answer - ${String(error)}`);
      }
      return void 0;
    }
  };

  // src/lib/pick.ts
  var resolveName = (serial, oplTimeout, prefix) => {
    const fromTooltip = (queryOPL(serial, oplTimeout, prefix)?.name ?? "").trim();
    return fromTooltip || (client.findObject(serial)?.name ?? "").trim();
  };
  var clicked = (prefix) => {
    target.cancel();
    const info = target.query();
    if (!(info?.serial ?? 0)) {
      target.cancel();
      log(`${prefix}: nothing targeted`, info);
      return void 0;
    }
    return info;
  };
  var describe = (info, oplTimeout, prefix) => {
    const serial = info.serial ?? 0;
    const found = client.findObject(serial);
    return {
      serial,
      name: resolveName(serial, oplTimeout, prefix),
      graphic: info.graphic ?? found?.graphic ?? 0,
      hue: info.hue ?? found?.hue ?? 0
    };
  };
  var pickOne = ({ prefix, prompt, oplTimeout }) => {
    log(`${prefix}: ${prompt}`);
    const info = clicked(prefix);
    return info && describe(info, oplTimeout, prefix);
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

  // src/animallore/config.ts
  var GOAL = 1e3;
  var LORE_GUMP_TEXT = "Loyalty Rating";
  var LORE_GUMP_BUTTON = void 0;
  var LORE_TIMEOUT = 2e3;
  var LORE_POLL = 150;
  var READ_DELAY = 1e3;
  var PACE_STEP = 400;
  var PACE_MAX = 8e3;
  var PACE_EASE_AFTER = 5;
  var SKILL_TIMEOUT = 5e3;
  var SKILL_POLL = 250;
  var MAX_BLIND_READS = 20;
  var MAX_AWAY = 20;
  var OPL_TIMEOUT = 1e3;
  var STALL_WARN = 100;
  var STALL_STOP = 1e3;
  var OUTCOME_TEXT = {
    // A failed skill check, and still the other half of the training: the roll happened either way
    missed: ["You can't think of anything you know offhand", "You cannot think of anything"],
    notAnimal: ["That's not an animal", "That is not an animal", "You have no idea what that is"],
    notYours: ["You can only lore tamed creatures"],
    tooFar: ["That is too far away", "You cannot see that", "Target cannot be seen"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };

  // src/animallore/gump.ts
  var refused = false;
  var closeLoreGump = (gump) => {
    gump.close();
    if (!gump.exists) {
      return;
    }
    if (LORE_GUMP_BUTTON !== void 0) {
      gump.reply(LORE_GUMP_BUTTON);
      return;
    }
    if (!refused) {
      refused = true;
      log(
        `lore: the gump did not close - find the id its X answers to and set LORE_GUMP_BUTTON, or the next read may be refused with one still on screen`
      );
    }
  };
  var closeStrayGump = () => {
    const found = Gump.findOrWait(LORE_GUMP_TEXT, 0);
    if (found) {
      closeLoreGump(found);
    }
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

  // src/animallore/guards.ts
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

  // src/animallore/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "lore",
    noun: "reads",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/animallore/lore.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var STOP_REASON = {
    notAnimal: "that is not something Animal Lore reads",
    notYours: "the shard only lores tamed creatures",
    unskilled: "not skilled enough to lore this creature"
  };
  var settled = () => {
    for (let waited = 0; waited < LORE_TIMEOUT; waited += LORE_POLL) {
      const gump = Gump.findOrWait(LORE_GUMP_TEXT, LORE_POLL);
      if (gump) {
        closeLoreGump(gump);
        return { opened: true };
      }
      const said = ALL_OUTCOME_TEXT.find((text) => journal.containsText(text));
      if (said) {
        return { said, opened: false };
      }
    }
    return { opened: false };
  };
  var loreOnce = (serial) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    journal.clear();
    player.useSkill(Skills.AnimalLore, serial);
    const { said, opened } = settled();
    if (said) {
      return outcomeFor(said) ?? "unknown";
    }
    return opened ? "lored" : "unknown";
  };

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

  // src/animallore/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/animallore/index.ts
  var picked = pickOne({
    prefix: "lore",
    prompt: "target the creature to read",
    oplTimeout: OPL_TIMEOUT
  }) ?? die("lore: nothing picked");
  var animal = client.findObject(picked.serial);
  if (!animal || !isMobile(animal)) {
    die(`lore: ${hex(picked.serial)} is not a creature`);
  }
  var skill = createSkillReader({
    skill: Skills.AnimalLore,
    label: "Animal Lore",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var start = skill.waitForSkill() ?? die("lore: the client is not reporting the skill");
  log(`lore: reading '${picked.name || hex(picked.serial)}' - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}`);
  var cap = skill.cap();
  if (cap !== void 0 && GOAL > cap) {
    log(`lore: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
  }
  var pace = createPace({
    floor: READ_DELAY,
    step: PACE_STEP,
    max: PACE_MAX,
    easeAfter: PACE_EASE_AFTER
  });
  var stall = createStallWatch({
    prefix: "lore",
    without: "cycles without a read",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  var reads = 0;
  var missed = 0;
  var throttled = 0;
  var away = 0;
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
    if (!client.findObject(picked.serial)) {
      stop = `'${picked.name || hex(picked.serial)}' is gone`;
      break;
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
    const outcome = loreOnce(picked.serial);
    if (outcome !== "throttled") {
      throttled = 0;
    }
    if (outcome !== "tooFar") {
      away = 0;
    }
    switch (outcome) {
      // Both rolled the skill, which is the whole of the training: a lore that fails its check still
      // asked the shard for one
      case "lored":
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
        log(`lore: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the read";
        }
        break;
      // A pet wanders off and wanders back, so this waits rather than stopping
      case "tooFar":
        away++;
        log(`lore: out of range (${away}/${MAX_AWAY}) - walk back to it`);
        if (away >= MAX_AWAY) {
          stop = "the creature stayed out of range";
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
          log("lore: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls");
        }
      }
    }
    if (reads >= reported + LOG_EVERY) {
      reported = reads;
      log(
        `lore: ${reads} reads, ${missed} of them missed, ${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`
      );
    }
    stall.endCycle(outcome, cycle, reads);
    stop = stop ?? stall.reason();
    sleep(pace.delay());
  }
  closeStrayGump();
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  var ended = skill.value();
  log(
    `lore: ${reads} reads, ${missed} missed, ${skill.name()} ${tenths(start)} -> ${ended === void 0 ? "unknown" : tenths(ended)}`
  );
  if (unread > 0) {
    log(`lore: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
  }
  log(`lore: stopping - ${reason}`);
  exit(`lore: ${reason}`);
})();
