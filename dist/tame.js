"use strict";
(() => {
  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var distanceTo = (spot) => Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));
  var isMobile = (entity) => entity._tag === "Mobile";
  var nameOf = (entity) => entity.name || hex(entity.serial);
  var approach = (serial, options) => {
    for (let taken = 0; taken < options.maxSteps; taken++) {
      const found = client.findObject(serial);
      if (!found || !isMobile(found)) {
        log(`${options.label}: lost track of ${hex(serial)}`);
        return void 0;
      }
      if (distanceTo(found) <= options.range) {
        return found;
      }
      if (!options.step(found) && !options.isSaving?.()) {
        log(`${options.label}: cannot reach ${nameOf(found)}`);
        return void 0;
      }
    }
    log(`${options.label}: still not next to ${hex(serial)} after ${options.maxSteps} steps`);
    return void 0;
  };

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);
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
  var pickOne = ({ prefix, prompt: prompt2, oplTimeout }) => {
    log(`${prefix}: ${prompt2}`);
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
          const reading2 = value();
          if (reading2 !== void 0) {
            return reading2;
          }
          sleep(pollMs);
        }
        return value();
      }
    };
  };

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var WALK_DELAY = 300;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var STALL_WARN = 60;
  var STALL_STOP = 300;
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

  // src/taming/config.ts
  var TAME_START_TIMEOUT = 3e3;
  var TAME_RESOLVE_TIMEOUT = 15e3;
  var TAME_WAIT_SLICE = 500;
  var TAME_RANGE = 2;
  var HUNT_RADIUS = 12;
  var TAME_APPROACH = 1;
  var TAME_MAX_STEPS = 40;
  var TAME_DELAY = 1500;
  var PACE_STEP = 400;
  var PACE_MAX = 8e3;
  var PACE_EASE_AFTER = 5;
  var ANGRY_DELAY = 1e4;
  var MAX_AWAY = 10;
  var MAX_CONTESTED = 20;
  var MAX_ANGRY = 10;
  var MAX_PENDING = 10;
  var HEALTH_FLOOR = 0.5;
  var SKILL_TIMEOUT = 5e3;
  var SKILL_POLL = 250;
  var OPL_TIMEOUT = 1e3;
  var PET_NAME = "sifinha";
  var AFTER_TAME = "kill";
  var KILL_MENU_TEXT = ["Kill", "Attack"];
  var KILL_CURSOR_TIMEOUT = 2e3;
  var KILL_PICK_TIMEOUT = 6e4;
  var KILL_PICK_POLL = 250;
  var MENU_TIMEOUT = 2e3;
  var PROMPT_TIMEOUT = 2e3;
  var RENAME_MENU_TEXT = ["Rename"];
  var RELEASE_MENU_TEXT = ["Release"];
  var RELEASE_CONFIRM_BUTTONS = [1, 2, 0];
  var RELEASE_CONFIRM_TEXT = ["release this creature", "release this", "Are you sure"];
  var RELEASE_CONFIRM_TIMEOUT = 1500;
  var RELEASE_CONFIRM_POLL = 150;
  var RELEASE_TIMEOUT = 3e3;
  var RELEASE_POLL = 250;
  var OUTCOME_TEXT = {
    tamed: ["It seems to accept you as master"],
    failed: ["You fail to tame the creature"],
    // Not a result: the attempt has been accepted and will answer in a few seconds
    starting: [
      "You start to tame the creature",
      "You continue to tame the creature",
      "You are already taming this creature"
    ],
    angry: ["is too angry to continue taming", "You have been interrupted"],
    contested: ["Someone else is already taming this creature"],
    alreadyTame: ["That animal looks tame already"],
    hopeless: ["You have no chance of taming this creature"],
    notAnimal: ["That creature cannot be tamed", "You can't tame that", "That wasn't a valid target"],
    tooFar: [
      "You must be closer to attempt to tame this creature",
      "You are too far away to continue taming",
      "That is too far away",
      "You cannot see that"
    ],
    // Below the specific refusals: UNSKILLED_TEXT ends in bare prefixes, and the first bucket holding
    // a match is the one that wins
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };

  // src/lib/vitals.ts
  var hitsCeiling = () => player.maxHits > 0 ? player.maxHits : void 0;

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var hurt = (fraction) => () => {
    const ceiling = hitsCeiling();
    if (ceiling === void 0) {
      return void 0;
    }
    return player.hits < ceiling * fraction ? `hurt (${player.hits}/${ceiling})` : void 0;
  };
  var firstReason = (...guards) => {
    for (const guard of guards) {
      const reason2 = guard();
      if (reason2) {
        return reason2;
      }
    }
    return void 0;
  };

  // src/taming/guards.ts
  var full = () => player.maxFollowers > 0 && player.followers >= player.maxFollowers ? "no follower slots left" : void 0;
  var stopReason = () => firstReason(dead, hurt(HEALTH_FLOOR), full);

  // src/taming/hunt.ts
  var skipped = /* @__PURE__ */ new Set();
  var leaveOut = (serial) => {
    skipped.add(serial);
  };
  var mine = (name) => PET_NAME !== "" && name.toLowerCase() === PET_NAME.toLowerCase();
  var named = (mobile) => {
    if (mobile.name) {
      return mobile.name;
    }
    return (queryOPL(mobile.serial, OPL_TIMEOUT, "tame")?.name ?? "").trim() || nameOf(mobile);
  };
  var nextQuarry = (graphic) => {
    if (HUNT_RADIUS <= 0) {
      return void 0;
    }
    const candidates = client.findAllMobilesOfType(graphic, null, null, null, HUNT_RADIUS).filter(
      (mobile) => (
        // graphic reads 0 for an entity the client is no longer tracking
        mobile.graphic !== 0 && !skipped.has(mobile.serial) && !mobile.isDead && // True for pets and followers, so this is every animal the run has already kept
        !mobile.isRenamable && // Measured rather than left to the scan's own range, whose meaning next to these arguments
        // is undocumented, where distanceTo is the Chebyshev the shard measures reach in
        distanceTo(mobile) <= HUNT_RADIUS && !mine(mobile.name)
      )
    ).sort((a, b) => distanceTo(a) - distanceTo(b));
    for (const mobile of candidates) {
      const name = named(mobile);
      if (mine(name)) {
        leaveOut(mobile.serial);
        continue;
      }
      return {
        quarry: { serial: mobile.serial, name, graphic: mobile.graphic },
        inSight: candidates.length
      };
    }
    return void 0;
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

  // src/taming/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "tame",
    noun: "attempts",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/menu.ts
  var chooseMenuEntry = (options) => {
    popupMenu.close();
    popupMenu.request(options.serial, options.timeoutMs);
    const content = popupMenu.waitForContent(options.timeoutMs);
    if (!content || content.serial !== options.serial) {
      popupMenu.close();
      return "noMenu";
    }
    const wanted = options.texts.map((text) => text.toLowerCase());
    const entry = content.items.find(
      (item) => wanted.some((text) => item.text.toLowerCase().includes(text))
    );
    if (!entry) {
      popupMenu.close();
      return "noEntry";
    }
    popupMenu.reply(entry.index);
    return "pressed";
  };

  // src/lib/retry.ts
  var settled = (options) => {
    for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
      sleep(options.pollMs);
      if (options.landed()) {
        return true;
      }
    }
    return false;
  };

  // src/taming/pet.ts
  var confirmButton;
  var saidNoGump = false;
  var saidNoButton = false;
  var isPet = (serial) => {
    const found = client.findObject(serial);
    return !!found && isMobile(found) && found.isRenamable;
  };
  var renamePet = (serial, name) => {
    const chosen = chooseMenuEntry({ serial, texts: RENAME_MENU_TEXT, timeoutMs: MENU_TIMEOUT });
    if (chosen !== "pressed") {
      return chosen;
    }
    if (!prompt.waitUntilOpen(PROMPT_TIMEOUT)) {
      return "noPrompt";
    }
    prompt.reply(name);
    return "renamed";
  };
  var findConfirm = (before) => {
    settled({
      timeoutMs: RELEASE_CONFIRM_TIMEOUT,
      pollMs: RELEASE_CONFIRM_POLL,
      landed: () => Gump.lastSerial !== before
    });
    const last = Gump.last;
    if (last?.exists) {
      return last;
    }
    for (const text of RELEASE_CONFIRM_TEXT) {
      const found = Gump.findOrWait(text, RELEASE_CONFIRM_POLL);
      if (found) {
        return found;
      }
    }
    return void 0;
  };
  var answerConfirm = (before, button) => {
    const gump = findConfirm(before);
    if (!gump) {
      if (!saidNoGump) {
        saidNoGump = true;
        log(
          `tame: found no gump to confirm the release with - lastSerial ${before} -> ${Gump.lastSerial}, last ${Gump.last ? `exists ${Gump.last.exists}` : "null"}`
        );
      }
      return;
    }
    if (!gump.hasButton(button) && !saidNoButton) {
      saidNoButton = true;
      log(`tame: the release gump does not admit to a button ${button} - pressing it anyway`);
    }
    gump.reply(button);
  };
  var releasePet = (serial) => {
    const buttons = confirmButton === void 0 ? RELEASE_CONFIRM_BUTTONS : [confirmButton];
    let pressed = false;
    for (const button of buttons) {
      const before = Gump.lastSerial;
      const chosen = chooseMenuEntry({ serial, texts: RELEASE_MENU_TEXT, timeoutMs: MENU_TIMEOUT });
      if (chosen === "noEntry" && pressed) {
        return "released";
      }
      if (chosen !== "pressed") {
        return pressed ? "stillPet" : chosen;
      }
      pressed = true;
      answerConfirm(before, button);
      const gone = settled({
        timeoutMs: RELEASE_TIMEOUT,
        pollMs: RELEASE_POLL,
        landed: () => !isPet(serial)
      });
      if (gone) {
        if (confirmButton === void 0) {
          confirmButton = button;
          log(`tame: the release gump answers to button ${button}`);
        }
        return "released";
      }
    }
    if (Gump.last?.exists) {
      Gump.last.close();
    }
    return "stillPet";
  };
  var commandKill = (serial, name) => {
    if (target.open) {
      target.cancel();
    }
    const chosen = chooseMenuEntry({ serial, texts: KILL_MENU_TEXT, timeoutMs: MENU_TIMEOUT });
    if (chosen !== "pressed") {
      return chosen;
    }
    if (!target.wait(KILL_CURSOR_TIMEOUT)) {
      return "noCursor";
    }
    log(`tame: told '${name}' to kill - pick its target`);
    const picked = settled({
      timeoutMs: KILL_PICK_TIMEOUT,
      pollMs: KILL_PICK_POLL,
      landed: () => !target.open
    });
    return picked ? "ordered" : "unanswered";
  };

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

  // src/taming/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/taming/tame.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var RESOLUTION_TEXT = ALL_OUTCOME_TEXT.filter(
    (text) => !OUTCOME_TEXT.starting.includes(text)
  );
  var STOP_REASON = {
    hopeless: "the shard says this creature cannot be tamed by you",
    notAnimal: "that is not something Animal Taming works on",
    alreadyTame: "that animal is already tame",
    unskilled: "not skilled enough to tame this creature"
  };
  var renamable = (serial) => {
    const found = client.findObject(serial);
    return !!found && isMobile(found) && found.isRenamable;
  };
  var waitOut = (texts, budgetMs, between) => {
    for (let waited = 0; waited < budgetMs; waited += TAME_WAIT_SLICE) {
      const matched = journal.waitForTextAny(texts, void 0, TAME_WAIT_SLICE);
      if (matched) {
        return matched;
      }
      between?.();
    }
    return null;
  };
  var settle = (serial, wasPet, between) => {
    const opened = waitOut(ALL_OUTCOME_TEXT, TAME_START_TIMEOUT, between);
    const first = opened ? outcomeFor(opened) ?? "unknown" : void 0;
    if (first && first !== "starting") {
      return first;
    }
    const settled2 = waitOut(RESOLUTION_TEXT, TAME_RESOLVE_TIMEOUT, between);
    if (settled2) {
      return outcomeFor(settled2) ?? "unknown";
    }
    if (!wasPet && renamable(serial)) {
      return "tamed";
    }
    return first === "starting" ? "pending" : "unknown";
  };
  var tameOnce = (serial, between) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    const wasPet = renamable(serial);
    journal.clear();
    player.useSkill(Skills.AnimalTaming, serial);
    return settle(serial, wasPet, between);
  };

  // src/lib/grid.ts
  var STEPS = [
    [0, -1],
    [1, -1],
    [1, 0],
    [1, 1],
    [0, 1],
    [-1, 1],
    [-1, 0],
    [-1, -1]
  ];

  // src/lib/walk.ts
  var DIRECTIONS = [
    Directions.North,
    Directions.Right,
    Directions.East,
    Directions.Down,
    Directions.South,
    Directions.Left,
    Directions.West,
    Directions.Up
  ];
  var indexOf = (step) => STEPS.findIndex(([x, y]) => x === step[0] && y === step[1]);
  var createStepToward = (options) => {
    const take = (step) => {
      const allowed = options.constrain ? options.constrain(step[0], step[1]) : step;
      if (allowed === void 0) {
        return false;
      }
      const at = indexOf(allowed);
      if (at < 0) {
        return false;
      }
      const beforeX = player.x;
      const beforeY = player.y;
      player.run(DIRECTIONS[at]);
      sleep(options.delayMs);
      player.run(DIRECTIONS[at]);
      sleep(options.delayMs);
      return player.x !== beforeX || player.y !== beforeY;
    };
    return (spot) => {
      const wantX = Math.sign(spot.x - player.x);
      const wantY = Math.sign(spot.y - player.y);
      const wanted = options.route?.(spot) ?? (wantX === 0 && wantY === 0 ? void 0 : [wantX, wantY]);
      if (wanted === void 0) {
        return false;
      }
      if (take(wanted)) {
        return true;
      }
      const at = indexOf(wanted);
      return at >= 0 && [STEPS[(at + 1) % STEPS.length], STEPS[(at + 7) % STEPS.length]].some(take);
    };
  };

  // src/taming/walk.ts
  var stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY });
  var distanceOf = (serial) => {
    const found = client.findObject(serial);
    return found && isMobile(found) ? distanceTo(found) : void 0;
  };
  var walkTo = (serial) => {
    const before = distanceOf(serial);
    const reached = approach(serial, {
      label: "tame",
      range: TAME_APPROACH,
      maxSteps: TAME_MAX_STEPS,
      step: stepToward,
      isSaving
    });
    if (reached) {
      return "closed";
    }
    const after = distanceOf(serial);
    return before !== void 0 && after !== void 0 && after < before ? "gained" : "stuck";
  };
  var keepUp = (serial) => {
    const found = client.findObject(serial);
    if (found && isMobile(found) && distanceTo(found) > TAME_RANGE) {
      stepToward(found);
    }
  };

  // src/taming/index.ts
  var skill = createSkillReader({
    skill: Skills.AnimalTaming,
    label: "Animal Taming",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var start = skill.waitForSkill();
  var reading = (value) => value === void 0 ? "unknown" : tenths(value);
  var pace = createPace({
    floor: TAME_DELAY,
    step: PACE_STEP,
    max: PACE_MAX,
    easeAfter: PACE_EASE_AFTER
  });
  var stall = createStallWatch({
    prefix: "tame",
    without: "cycles without an attempt",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  log(`tame: ${skill.name()} at ${reading(start)}`);
  var tamed = 0;
  var attempts = 0;
  var lastValue = start;
  var failures = 0;
  var reported = 0;
  var stop;
  var unread = 0;
  var unnamed = 0;
  var unfinished = 0;
  var unreadSaid = false;
  var afterTame = (serial, name) => {
    let called = name;
    if (PET_NAME) {
      const renamed = renamePet(serial, PET_NAME);
      if (renamed === "renamed") {
        called = PET_NAME;
        log(`tame: renamed '${name}' to '${PET_NAME}'`);
      } else {
        unnamed++;
        log(`tame: could not rename '${name}' (${renamed}) - carrying on`);
      }
    }
    if (AFTER_TAME === "kill") {
      const ordered = commandKill(serial, called);
      if (ordered !== "ordered") {
        unfinished++;
        log(`tame: could not order '${called}' to kill (${ordered}) - carrying on`);
      }
      return;
    }
    if (AFTER_TAME !== "release") {
      return;
    }
    const released = releasePet(serial);
    if (released === "released") {
      log(`tame: released '${called}'`);
    } else {
      unfinished++;
      log(`tame: could not release '${called}' (${released}) - carrying on`);
    }
  };
  var hunting;
  while (!stop) {
    const sighted = hunting === void 0 ? void 0 : nextQuarry(hunting);
    let quarry = sighted?.quarry;
    if (!quarry) {
      const picked = pickOne({
        prefix: "tame",
        prompt: "target the creature to tame",
        oplTimeout: OPL_TIMEOUT
      });
      if (!picked) {
        stop = tamed > 0 ? `${tamed} tamed` : "nothing picked";
        break;
      }
      const animal = client.findObject(picked.serial);
      if (!animal || !isMobile(animal)) {
        log(`tame: ${hex(picked.serial)} is not a creature`);
        continue;
      }
      hunting = picked.graphic || animal.graphic || void 0;
      quarry = { serial: picked.serial, name: nameOf(picked), graphic: hunting ?? 0 };
    }
    const name = quarry.name;
    const others = (sighted?.inSight ?? 1) - 1;
    log(`tame: taming '${name}'${others > 0 ? ` (${others} more in sight)` : ""}`);
    let done;
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
      if (isSaving()) {
        waitOutSave();
        throttled = 0;
        stall.progressed();
        stall.endCycle("saving", cycle, attempts);
        continue;
      }
      const found = client.findObject(quarry.serial);
      if (!found || !isMobile(found)) {
        done = `'${name}' is gone`;
        break;
      }
      if (distanceTo(found) > TAME_RANGE) {
        if (walkTo(quarry.serial) !== "stuck") {
          away = 0;
        } else if (++away >= MAX_AWAY) {
          done = `could not get near '${name}'`;
          break;
        }
        beat("walking", cycle, attempts);
        stall.endCycle("walking", cycle, attempts);
        stop = stop ?? stall.reason();
        continue;
      }
      const value = skill.value();
      if (value !== void 0 && value !== lastValue) {
        lastValue = value;
        unreadSaid = false;
        stall.progressed();
      }
      const outcome = tameOnce(quarry.serial, () => keepUp(quarry.serial));
      if (outcome !== "throttled") {
        throttled = 0;
      }
      if (outcome !== "tooFar") {
        away = 0;
      }
      if (outcome !== "contested") {
        contested = 0;
      }
      if (outcome !== "angry") {
        angry = 0;
      }
      if (outcome !== "pending") {
        pending = 0;
      }
      switch (outcome) {
        case "tamed":
          attempts++;
          tamed++;
          stall.progressed();
          accepted = true;
          done = `'${name}' accepted you as master`;
          break;
        // A failed tame still rolled the skill, which is the ordinary cycle rather than a refusal
        case "failed":
          attempts++;
          failures++;
          unreadSaid = false;
          pace.landed();
          stall.progressed();
          break;
        // The shard took the attempt and never answered. Raise TAME_RESOLVE_TIMEOUT if this run ends
        // here.
        case "pending":
          attempts++;
          pending++;
          if (pending >= MAX_PENDING) {
            stop = "attempts kept starting and never resolving";
          }
          break;
        case "angry":
          angry++;
          log(`tame: '${name}' is too angry (${angry}/${MAX_ANGRY}), letting it settle`);
          sleep(ANGRY_DELAY);
          if (angry >= MAX_ANGRY) {
            done = `'${name}' stayed too angry to tame`;
          }
          break;
        case "contested":
          contested++;
          log(`tame: someone else has '${name}' (${contested}/${MAX_CONTESTED})`);
          if (contested >= MAX_CONTESTED) {
            done = `another tamer has '${name}'`;
          }
          break;
        // Walked at rather than waited out, so a creature that bolted mid-attempt is chased
        case "tooFar":
          if (walkTo(quarry.serial) !== "stuck") {
            away = 0;
          } else if (++away >= MAX_AWAY) {
            done = `could not get near '${name}'`;
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
          log(`tame: shard says wait (${throttled}/${MAX_THROTTLED}), now pacing at ${pace.refused()}ms`);
          sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
          if (throttled >= MAX_THROTTLED) {
            stop = "the shard kept refusing the attempt";
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
            log("tame: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls");
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
    if (done) {
      log(`tame: ${done}`);
    } else if (!stop) {
      log(`tame: hit the ${MAX_CYCLES} cycle backstop on '${name}'`);
    }
    if (accepted) {
      afterTame(quarry.serial, name);
    }
    leaveOut(quarry.serial);
  }
  var reason = stop ?? "the session ended";
  log(
    `tame: ${tamed} tamed over ${attempts} attempts, ${failures} failed, ${skill.name()} ${reading(start)} -> ${reading(skill.value())}`
  );
  if (unread > 0) {
    log(`tame: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
  }
  if (unnamed > 0 || unfinished > 0) {
    log(
      `tame: ${unnamed} rename(s) and ${unfinished} ${AFTER_TAME} order(s) did not go through - check the menu wordings in config against the menu the shard sends`
    );
  }
  log(`tame: stopping - ${reason}`);
  exit(`tame: ${reason}`);
})();
