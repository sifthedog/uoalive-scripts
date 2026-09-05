"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var nameOf = (entity) => entity.name || hex(entity.serial);

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

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var TARGET_TIMEOUT = 2e3;
  var EQUIP_TIMEOUT = 2e3;
  var EQUIP_POLL = 200;
  var EQUIP_ATTEMPTS = 3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var MAX_NO_CURSOR = 20;
  var NO_CURSOR_READ = 500;
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

  // src/lockpicking/config.ts
  var GOAL = 1e3;
  var LOCKPICK_GRAPHICS = /* @__PURE__ */ new Set([5371]);
  var LOCKPICK_NAME = "lockpick";
  var POKE_BOX = true;
  var POKE_DELAY = 600;
  var ATTEMPT_DELAY = 1200;
  var PICK_TIMEOUT = 5e3;
  var SKILL_TIMEOUT = 5e3;
  var SKILL_POLL = 250;
  var MAX_BLIND_READS = 20;
  var STALL_WARN = 100;
  var STALL_STOP = 1e3;
  var OPL_TIMEOUT = 1e3;
  var OUTCOME_TEXT = {
    // What training is made of: a lock that will not open still rolls the skill
    failed: ["You are unable to pick the lock"],
    broke: ["You broke the lockpick", "You have broken your lockpick", "You broke your lockpick"],
    picked: ["You successfully pick the lock", "You pick the lock"],
    // Before the bare wordings UNSKILLED_TEXT ends with, since outcomeFor takes the first bucket that matches
    tooHard: ["This lock cannot be picked by you", "The lock is too complex", ...UNSKILLED_TEXT],
    notLocked: ["This does not appear to be locked", "That does not appear to be locked"],
    tooFar: ["That is too far away", "You cannot reach that"],
    noPicks: ["You do not have any lockpicks"],
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };

  // src/lib/containers.ts
  var CONTAINER_GRAPHICS = /* @__PURE__ */ new Set([
    3701,
    // backpack
    3702,
    // bag
    3705,
    // pouch
    3709,
    // wooden box
    3651,
    // wooden chest
    2472,
    // metal box
    2475,
    // metal chest
    3644,
    // crate
    3645,
    // crate
    3648,
    // gold chest
    3649
    // gold chest
  ]);
  var unreadable = /* @__PURE__ */ new Set();
  var complained = /* @__PURE__ */ new Set();
  var packComplained = false;
  var forgetUnreadable = (serial) => {
    if (serial === void 0) {
      unreadable.clear();
      return;
    }
    unreadable.delete(serial);
  };
  var describe2 = (item) => {
    try {
      return `${hex(item.serial)} ${hex(item.graphic)} '${item.name ?? ""}'`;
    } catch {
      return `${hex(item.serial)} which will not say what it is`;
    }
  };
  var contentsOf = (item) => {
    if (!item || unreadable.has(item.serial)) {
      return void 0;
    }
    try {
      return item.contents;
    } catch (error) {
      unreadable.add(item.serial);
      if (!complained.has(item.serial)) {
        complained.add(item.serial);
        log(`contents: ${describe2(item)} would not answer - ${String(error)}`);
      }
      return void 0;
    }
  };
  var packContents = () => {
    try {
      const pack = player.backpack;
      forgetUnreadable(pack?.serial);
      return contentsOf(pack);
    } catch (error) {
      if (!packComplained) {
        packComplained = true;
        log(`contents: the backpack would not answer - ${String(error)}`);
      }
      return void 0;
    }
  };
  var isContainer = (item) => (contentsOf(item)?.length ?? 0) > 0 || CONTAINER_GRAPHICS.has(item.graphic);
  var openContainers = (preferredSerial) => {
    if (preferredSerial) {
      player.use(preferredSerial);
      sleep(800);
      forgetUnreadable(preferredSerial);
      return true;
    }
    let opened = false;
    for (const item of packContents() ?? []) {
      if (!isContainer(item)) {
        continue;
      }
      player.use(item.serial);
      sleep(800);
      forgetUnreadable(item.serial);
      opened = true;
    }
    return opened;
  };
  var findIn = (contents, matches) => {
    for (const item of contents ?? []) {
      if (matches(item)) {
        return item;
      }
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        const foundInSub = findIn(sub, matches);
        if (foundInSub) return foundInSub;
      }
    }
    return null;
  };

  // src/lib/pack.ts
  var totalMatching = (matches, contents = packContents()) => (contents ?? []).reduce(
    (total, item) => total + (matches(item) ? item.amount ?? 1 : 0) + totalMatching(matches, contentsOf(item) ?? []),
    0
  );

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
  var untilLanded = (options) => {
    for (let attempt = 1; attempt <= options.attempts; attempt++) {
      options.act();
      if (settled(options)) {
        return true;
      }
      log(`${options.label}: attempt ${attempt} did not land, reissuing`);
    }
    log(`${options.label}: gave up`);
    return false;
  };

  // src/lib/tool.ts
  var describeContents = (contents) => (contents ?? []).map((item) => {
    const sub = contentsOf(item);
    return sub?.length ? `${hex(item.graphic)}[${describeContents(sub)}]` : hex(item.graphic);
  }).join(", ");
  var createTool = (options) => {
    let learned;
    let spareBagSerial = options.spareBagSerial;
    let reportedEmpty = false;
    const is = (item) => learned !== void 0 && item.graphic === learned || (options.graphics?.has(item.graphic) ?? false) || (item.name ?? "").toLowerCase().includes(options.name);
    const remember = (item) => {
      if (item && learned === void 0) {
        learned = item.graphic;
        log(`${options.label}: graphic is ${hex(item.graphic)}`);
      }
    };
    const reportEmptyPack = () => {
      if (reportedEmpty) {
        return;
      }
      log(`${options.label}: none found. Pack holds: ${describeContents(packContents())}`);
      log(`${options.label}: if the spares are in a bag inside a bag, pin it as SPARE_BAG_SERIAL`);
      reportedEmpty = true;
    };
    const find = () => {
      let found = findIn(packContents(), is);
      if (!found && openContainers(spareBagSerial)) {
        found = findIn(packContents(), is);
      }
      if (!found) {
        reportEmptyPack();
        return void 0;
      }
      reportedEmpty = false;
      remember(found);
      if (found.container && found.container !== player.backpack?.serial) {
        spareBagSerial = found.container;
      }
      return found;
    };
    const stillHolding = () => {
      const item = options.held();
      return !!item && is(item) && client.findObject(item.serial) !== void 0;
    };
    return {
      is,
      remember,
      find,
      serial: () => options.held()?.serial,
      equip: () => {
        if (stillHolding()) {
          return true;
        }
        const found = find();
        if (!found) {
          client.headMsg(`No ${options.name}!`, player, 33);
          return false;
        }
        target.cancel();
        return untilLanded({
          label: `equip ${options.name}`,
          attempts: options.equip.attempts,
          timeoutMs: options.equip.timeoutMs,
          pollMs: options.equip.pollMs,
          act: () => player.equip(found.serial),
          landed: () => options.held()?.serial === found.serial
        });
      }
    };
  };

  // src/lockpicking/picks.ts
  var tool = /* @__PURE__ */ createTool({
    label: "lockpicks",
    name: LOCKPICK_NAME,
    graphics: LOCKPICK_GRAPHICS,
    // Used out of the pack rather than worn, so no layer answers for them and equip() is never called
    held: () => void 0,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL }
  });
  var findLockpick = tool.find;
  var lockpickTotal = () => totalMatching(tool.is);

  // src/lockpicking/attempt.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var STOP_REASON = {
    picked: "the lock is open - a box that will not lock again cannot train anything",
    tooHard: "the shard says this lock is beyond you",
    notLocked: "that container is not locked",
    tooFar: "stand next to the container",
    noPicks: "out of lockpicks"
  };
  var silentOutcome = (before) => lockpickTotal() < before ? "broke" : "unknown";
  var refusedOutcome = (boxSerial, before) => {
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, NO_CURSOR_READ);
    if (matched) {
      return outcomeFor(matched);
    }
    const silent = silentOutcome(before);
    if (silent !== "unknown") {
      return silent;
    }
    log(`pickOnce: no target cursor for ${hex(boxSerial)} - is the lockpick still in the pack?`);
    return "noCursor";
  };
  var pickOnce = (boxSerial, lockpickSerial) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    if (POKE_BOX) {
      player.use(boxSerial);
      sleep(POKE_DELAY);
    }
    const before = lockpickTotal();
    journal.clear();
    player.use(lockpickSerial);
    if (!target.waitTargetEntity(boxSerial, TARGET_TIMEOUT)) {
      target.cancel();
      return refusedOutcome(boxSerial, before);
    }
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, PICK_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(before);
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

  // src/lockpicking/guards.ts
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

  // src/lockpicking/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "lockpick",
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

  // src/lockpicking/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/lockpicking/index.ts
  var box = pickOne({
    prefix: "lockpick",
    prompt: "target the locked container to pick",
    oplTimeout: OPL_TIMEOUT
  }) ?? die("lockpick: nothing to pick");
  var skill = createSkillReader({
    skill: Skills.Lockpicking,
    label: "Lockpicking",
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var start = skill.waitForSkill() ?? die("lockpick: the client is not reporting the skill");
  log(
    `lockpick: ${nameOf(box)} - ${skill.name()} at ${tenths(start)}/${tenths(GOAL)}, ${lockpickTotal()} lockpicks`
  );
  var cap = skill.cap();
  if (cap !== void 0 && GOAL > cap) {
    log(`lockpick: the shard caps ${skill.name()} at ${tenths(cap)} - it will not reach ${tenths(GOAL)}`);
  }
  var stall = createStallWatch({
    prefix: "lockpick",
    without: "cycles without an attempt",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  var attempts = 0;
  var broken = 0;
  var throttled = 0;
  var noCursor = 0;
  var blind = 0;
  var reported = 0;
  var lastValue = start;
  var stop;
  var unread = 0;
  var unreadPending = 0;
  var unreadSaid = false;
  var cleared = () => {
    unreadSaid = false;
    throttled = 0;
    noCursor = 0;
  };
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (isSaving()) {
      waitOutSave();
      cleared();
      stall.progressed();
      stall.endCycle("saving", cycle, attempts);
      continue;
    }
    const value = skill.value();
    if (value === void 0) {
      blind++;
      if (blind >= MAX_BLIND_READS) {
        stop = "the client stopped reporting the skill";
        break;
      }
      beat("unreadable skill", cycle, attempts);
      sleep(ATTEMPT_DELAY);
      continue;
    }
    blind = 0;
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
      stop = "out of lockpicks";
      break;
    }
    const outcome = pickOnce(box.serial, lockpick.serial);
    if (outcome !== "throttled") {
      throttled = 0;
    }
    if (outcome !== "noCursor") {
      noCursor = 0;
    }
    switch (outcome) {
      // Both rolled the skill, which is the whole of the training
      case "broke":
      case "failed":
        attempts++;
        unreadSaid = false;
        stall.progressed();
        if (outcome === "broke") {
          broken++;
        }
        break;
      case "saving":
        waitOutSave();
        cleared();
        stall.progressed();
        break;
      case "throttled":
        throttled++;
        log(`lockpick: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the attempt";
        }
        break;
      case "noCursor":
        noCursor++;
        log(`lockpick: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
        sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (noCursor >= MAX_NO_CURSOR) {
          stop = "the shard never opened a target cursor";
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
          log("lockpick: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls");
        }
      }
    }
    if (attempts >= reported + LOG_EVERY) {
      reported = attempts;
      log(
        `lockpick: ${attempts} attempts, ${broken} broken, ${lockpickTotal()} left, ${skill.name()} at ${tenths(value)}/${tenths(GOAL)}`
      );
    }
    stall.endCycle(outcome ?? "unknown", cycle, attempts);
    stop = stop ?? stall.reason();
    sleep(ATTEMPT_DELAY);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  var ended = skill.value();
  log(
    `lockpick: ${attempts} attempts, ${broken} lockpicks broken, ${skill.name()} ${tenths(start)} -> ${ended === void 0 ? "unknown" : tenths(ended)}`
  );
  if (unread > 0) {
    log(`lockpick: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
  }
  log(`lockpick: stopping - ${reason}`);
  exit(`lockpick: ${reason}`);
})();
