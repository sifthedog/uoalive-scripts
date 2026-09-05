"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var distanceTo = (spot) => Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));
  var isMobile = (entity) => entity._tag === "Mobile";

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);
  var createStallWatch = (options) => {
    let since = 0;
    let reason;
    return {
      endCycle: (phase, cycle, tally) => {
        options.heartbeat.beat(phase, cycle, tally);
        since++;
        if (since === options.warnAt) {
          log(`${options.prefix}: ${options.warnAt} ${options.without}, last was '${phase}'`);
        }
        if (since >= options.stopAt) {
          reason = `no progress in ${options.stopAt} cycles, last was '${phase}'`;
        }
      },
      progressed: () => {
        since = 0;
      },
      reason: () => reason
    };
  };

  // src/lib/harvest.ts
  var runHarvest = ({
    prefix,
    landed: landed2,
    toolName,
    stopReason: stopReason2,
    watch,
    equipTool,
    ready,
    relieve,
    approach,
    harvest,
    onLanded,
    handle: handle2,
    progress,
    finish,
    isSaving: isSaving2,
    waitOutSave: waitOutSave2,
    stall,
    timings
  }) => {
    let tally = 0;
    let unknown = 0;
    let stop;
    let reported = 0;
    let throttled = 0;
    let noCursor = 0;
    let noTool = 0;
    let idled = 0;
    const endCycle = (phase, cycle) => {
      stall.endCycle(phase, cycle, tally);
      stop ?? (stop = stall.reason());
    };
    try {
      for (let cycle = 0; cycle - idled < timings.maxCycles && !stop; cycle++) {
        stop = stopReason2();
        if (stop) {
          break;
        }
        if (isSaving2()) {
          waitOutSave2();
          unknown = 0;
          throttled = 0;
          stall.progressed();
          endCycle("saving", cycle);
          continue;
        }
        watch?.();
        stop = ready?.();
        if (stop) {
          break;
        }
        if (!equipTool()) {
          noTool++;
          if (noTool >= timings.maxNoTool) {
            stop = `no ${toolName}`;
            break;
          }
          log(`${prefix}: no ${toolName} (${noTool}/${timings.maxNoTool}), looking again`);
          endCycle("no tool", cycle);
          sleep(backoffFor(noTool, timings.throttleBackoff, timings.throttleBackoffMax));
          continue;
        }
        noTool = 0;
        const relieved = relieve?.();
        if (relieved) {
          if ("stop" in relieved) {
            stop = relieved.stop;
            break;
          }
          endCycle(relieved.phase, cycle);
          sleep(timings.stepDelay);
          continue;
        }
        let target2;
        if (approach) {
          const found = approach();
          if ("stop" in found) {
            stop = found.stop;
            break;
          }
          if ("waited" in found) {
            idled++;
            stall.progressed();
            continue;
          }
          if ("walked" in found) {
            endCycle("walking", cycle);
            continue;
          }
          target2 = found.target;
        }
        const outcome = harvest(target2);
        if (outcome === landed2) {
          tally++;
          unknown = 0;
          throttled = 0;
          stall.progressed();
          onLanded?.();
        } else {
          switch (outcome) {
            case "wornOut":
              log(`${prefix}: ${toolName} worn out, swapping`);
              unknown = 0;
              break;
            // The counters are reset rather than left alone, because whatever they had accumulated was
            // measured against a server that was not answering. The stall watchdog goes with them: a
            // shard that saves often would otherwise walk a run to its stop a save at a time.
            case "saving":
              waitOutSave2();
              unknown = 0;
              throttled = 0;
              stall.progressed();
              break;
            case "throttled":
              throttled++;
              unknown = 0;
              log(`${prefix}: shard says wait (${throttled}/${timings.maxThrottled}), backing off`);
              sleep(backoffFor(throttled, timings.throttleBackoff, timings.throttleBackoffMax));
              if (throttled >= timings.maxThrottled) {
                stop = "the shard kept refusing the swing";
              }
              break;
            // With a tool demonstrably in hand this is the shard declining to start the swing, which on
            // a live run was a third of them. The swing has already looked for a reason, so this is a
            // refusal with nothing said about it - backed off like one, on a budget of its own.
            case "noCursor":
              noCursor++;
              log(`${prefix}: no target cursor (${noCursor}/${timings.maxNoCursor}), backing off`);
              sleep(backoffFor(noCursor, timings.throttleBackoff, timings.throttleBackoffMax));
              if (noCursor >= timings.maxNoCursor) {
                stop = "the shard never opened a target cursor";
              }
              break;
            default: {
              const handled = outcome === void 0 ? void 0 : handle2(outcome, target2);
              if (handled) {
                unknown = 0;
                stop ?? (stop = handled.stop);
              } else {
                unknown++;
                log(
                  `${prefix}: unreadable outcome (${unknown}/${timings.maxUnknown}), check OUTCOME_TEXT`
                );
              }
            }
          }
        }
        if (outcome !== "noCursor") {
          noCursor = 0;
        }
        if (unknown >= timings.maxUnknown) {
          stop = `${timings.maxUnknown} unreadable outcomes in a row`;
          break;
        }
        if (tally >= reported + timings.logEvery) {
          reported = tally;
          log(`${prefix}: ${progress(tally)}, ${player.weight}/${player.weightMax}`);
        }
        endCycle(outcome ?? "unknown", cycle);
        sleep(timings.stepDelay);
      }
    } catch (error) {
      stop ?? (stop = `threw - ${String(error)}`);
    }
    const reason = stop ?? `hit the ${timings.maxCycles} working cycle backstop`;
    finish?.(tally, reason);
    log(`${prefix}: stopping - ${reason}`);
    exit(`${prefix}: ${reason}`);
  };

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var STEP_DELAY = 300;
  var TARGET_TIMEOUT = 2e3;
  var EQUIP_TIMEOUT = 2e3;
  var EQUIP_POLL = 200;
  var EQUIP_ATTEMPTS = 3;
  var HEARTBEAT_EVERY = 3e4;
  var STALL_WARN = 60;
  var STALL_STOP = 300;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var MAX_UNKNOWN = 5;
  var MAX_NO_CURSOR = 20;
  var NO_CURSOR_READ = 500;
  var MAX_NO_TOOL = 10;
  var PACK_LIMIT = 120;
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
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

  // src/lib/arts.ts
  var CORPSE_GRAPHIC = 8198;

  // src/carving/config.ts
  var MAX_CYCLES = 1e5;
  var KNIFE_NAME = "knife";
  var SPARE_BAG_SERIAL = void 0;
  var KNIFE_GRAPHICS = /* @__PURE__ */ new Set([
    5110,
    // butcher knife
    5111,
    // butcher knife
    3780,
    // cleaver
    3781,
    // cleaver
    3921,
    // dagger
    3922,
    // dagger
    4324,
    // skinning knife
    4325
    // skinning knife
  ]);
  var TAKE_GRAPHICS = /* @__PURE__ */ new Set([
    7121
    // feather
  ]);
  var LOOT_CORPSES = true;
  var CARVE_RANGE = 2;
  var CARVE_TIMEOUT = 3e3;
  var WATCH_POLL = 400;
  var OPEN_DELAY = 800;
  var MOVE_DELAY = 250;
  var SETTLE_TIMEOUT = 2e3;
  var SETTLE_POLL = 100;
  var PRUNE_EVERY = 50;
  var BLOCKED_DELAY = 6e4;
  var WEIGHT_BUFFER = 20;
  var OUTCOME_TEXT = {
    carved: [
      "You pluck the bird",
      "Feathers now go into your pack",
      "You carve away",
      "You carve some",
      "You skin the"
    ],
    nothingLeft: [
      "You see nothing useful to carve from the corpse",
      "There is nothing left to carve"
    ],
    notCarvable: [
      "You can't use a bladed item on that",
      "You cannot carve that",
      "That is not a corpse"
    ],
    tooFar: ["That is too far away", "You cannot reach that"],
    notSeen: ["Target cannot be seen"],
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };

  // src/carving/carve.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var refusedOutcome = () => {
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, NO_CURSOR_READ);
    return matched ? outcomeFor(matched) : "noCursor";
  };
  var carveOnce = (corpse, knifeSerial2) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    journal.clear();
    player.use(knifeSerial2);
    if (!target.waitTargetEntity(corpse.serial, TARGET_TIMEOUT)) {
      target.cancel();
      return refusedOutcome();
    }
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CARVE_TIMEOUT);
    return matched ? outcomeFor(matched) : "unknown";
  };

  // src/lib/store.ts
  var scope = globalThis;
  var createStore = (options) => {
    let held2;
    const load = () => {
      const found = scope[options.key];
      if (found?.version === options.version) {
        const described = options.describe?.(found);
        if (described) {
          log(described);
        }
        return found;
      }
      const fresh = { ...options.seed(), version: options.version };
      scope[options.key] = fresh;
      return fresh;
    };
    return {
      // Read through a call rather than handed out as the object itself, so forget() can actually
      // forget: a module-scope `const memory = load()` would give every importer a reference that
      // outlives it.
      read: () => held2 ?? (held2 = load()),
      // vi.resetModules() gives each test a fresh module registry but leaves globalThis alone, which
      // is precisely what this store is designed to survive.
      forget: () => {
        delete scope[options.key];
        held2 = void 0;
      }
    };
  };

  // src/carving/memory.ts
  var KEY = "__carving_memory";
  var VERSION = 1;
  var store = /* @__PURE__ */ createStore({
    key: KEY,
    version: VERSION,
    seed: () => ({ done: /* @__PURE__ */ new Set(), emptied: /* @__PURE__ */ new Set(), blocked: /* @__PURE__ */ new Map() }),
    describe: (found) => found.done.size > 0 ? `memory: resuming with ${found.done.size} corpses already dealt with` : void 0
  });
  var memory = store.read;
  var forget = store.forget;

  // src/carving/corpses.ts
  var onGround = () => client.findAllItemsOfType(CORPSE_GRAPHIC, void 0, "world").filter((item) => item.graphic !== 0);
  var inReach = (corpses, range) => corpses.filter((corpse) => distanceTo(corpse) <= range);
  var nearest = (corpses) => corpses.reduce(
    (best, corpse) => Math.min(distanceTo(corpse), best ?? Infinity),
    void 0
  );
  var prune = () => {
    const { done, emptied, blocked } = memory();
    for (const serial of [...done, ...emptied]) {
      if (!client.findObject(serial)) {
        done.delete(serial);
        emptied.delete(serial);
      }
    }
    const time = now();
    for (const [serial, until] of blocked) {
      if (time >= until || !client.findObject(serial)) {
        blocked.delete(serial);
      }
    }
  };
  var isBlocked = (serial) => {
    const until = memory().blocked.get(serial);
    return until !== void 0 && now() < until;
  };
  var nextToCarve = (corpses) => {
    const { done } = memory();
    return corpses.filter((corpse) => !done.has(corpse.serial) && !isBlocked(corpse.serial)).sort((a, b) => distanceTo(a) - distanceTo(b))[0];
  };
  var describeGround = () => `${hex(CORPSE_GRAPHIC)} x${onGround().length}`;

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
  var describe = (item) => {
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
        log(`contents: ${describe(item)} would not answer - ${String(error)}`);
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
  var collectIn = (contents, matches) => {
    const found = [];
    for (const item of contents ?? []) {
      if (matches(item)) {
        found.push(item);
      }
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        found.push(...collectIn(sub, matches));
      }
    }
    return found;
  };

  // src/lib/weight.ts
  var overweight = (buffer = 0) => player.weightMax > 0 && player.weight > player.weightMax - buffer;

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var heavy = (buffer) => () => overweight(buffer) ? `overweight (${player.weight}/${player.weightMax})` : void 0;
  var packFull = (limit) => () => {
    const top = (packContents() ?? []).length;
    return top >= limit ? `pack is full (${top} items at the top level)` : void 0;
  };
  var firstReason = (...guards) => {
    for (const guard of guards) {
      const reason = guard();
      if (reason) {
        return reason;
      }
    }
    return void 0;
  };

  // src/carving/guards.ts
  var stopReason = () => firstReason(dead, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));

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

  // src/carving/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "carve",
    noun: "carved",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

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
    let learned2;
    let spareBagSerial = options.spareBagSerial;
    let reportedEmpty = false;
    const is = (item) => learned2 !== void 0 && item.graphic === learned2 || (options.graphics?.has(item.graphic) ?? false) || (item.name ?? "").toLowerCase().includes(options.name);
    const remember = (item) => {
      if (item && learned2 === void 0) {
        learned2 = item.graphic;
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

  // src/carving/knife.ts
  var inHand = () => {
    const hand = player.equippedItems.oneHanded;
    return hand && knife.is(hand) ? hand : void 0;
  };
  var knife = /* @__PURE__ */ createTool({
    label: "knife",
    name: KNIFE_NAME,
    graphics: KNIFE_GRAPHICS,
    spareBagSerial: SPARE_BAG_SERIAL,
    held: inHand,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL }
  });
  var learned;
  var knifeSerial = () => {
    if (learned !== void 0 && client.findObject(learned)) {
      return learned;
    }
    learned = (inHand() ?? knife.find())?.serial;
    return learned;
  };

  // src/carving/loot.ts
  var wanted = (item) => TAKE_GRAPHICS.has(item.graphic);
  var corpseAt = (serial) => {
    const found = client.findObject(serial);
    return found && !isMobile(found) ? found : void 0;
  };
  var held = (serial) => contentsOf(corpseAt(serial));
  var landed = (serial, moved) => {
    const left = new Set((held(serial) ?? []).map((item) => item.serial));
    const gone = moved.filter((item) => !left.has(item.serial));
    return {
      stacks: gone.length,
      items: gone.reduce((total, item) => total + (item.amount ?? 1), 0)
    };
  };
  var settle = (serial, moved) => {
    let took = landed(serial, moved);
    for (let waited = 0; waited < SETTLE_TIMEOUT && took.stacks < moved.length; waited += SETTLE_POLL) {
      sleep(SETTLE_POLL);
      took = landed(serial, moved);
    }
    return took;
  };
  var pending = (corpses) => {
    const { done, emptied } = memory();
    return corpses.find(
      (corpse) => done.has(corpse.serial) && !emptied.has(corpse.serial) && !isBlocked(corpse.serial)
    );
  };
  var take = (corpse, packSerial2) => {
    player.use(corpse.serial);
    sleep(OPEN_DELAY);
    forgetUnreadable(corpse.serial);
    const { emptied } = memory();
    const contents = held(corpse.serial);
    if (contents === void 0) {
      emptied.add(corpse.serial);
      log(`carve: ${hex(corpse.serial)} would not say what it holds, leaving it`);
      return { stacks: 0, items: 0 };
    }
    const stacks = collectIn(contents, wanted);
    if (stacks.length === 0) {
      emptied.add(corpse.serial);
      return { stacks: 0, items: 0 };
    }
    stacks.forEach((item, index) => {
      if (index > 0) {
        sleep(MOVE_DELAY);
      }
      player.moveItem(item.serial, packSerial2);
    });
    const took = settle(corpse.serial, stacks);
    if (took.stacks === stacks.length) {
      emptied.add(corpse.serial);
    } else {
      memory().blocked.set(corpse.serial, now() + BLOCKED_DELAY);
      log(
        `carve: ${hex(corpse.serial)} kept ${stacks.length - took.stacks} of them, leaving it for ${BLOCKED_DELAY / 1e3}s`
      );
    }
    return took;
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

  // src/carving/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    onDone: resetBeat
  });

  // src/carving/index.ts
  var packSerial = player.backpack?.serial ?? die("carve: no backpack to put the feathers in");
  log(`carve: watching within ${CARVE_RANGE} tiles - ${describeGround()} in the world`);
  var carved = 0;
  var taken = 0;
  var waits = 0;
  var saidOutOfReach = false;
  var setAside = (corpse, why) => {
    memory().blocked.set(corpse.serial, now() + BLOCKED_DELAY);
    log(`carve: ${hex(corpse.serial)} ${why}, leaving it for ${BLOCKED_DELAY / 1e3}s`);
    return {};
  };
  var handle = (outcome, corpse) => {
    if (!corpse) {
      return void 0;
    }
    const { done, emptied } = memory();
    switch (outcome) {
      // Nothing left to carve is not nothing left to take: a corpse someone else carved, or one this
      // run carved before its memory was lost, can still be holding the feathers.
      case "nothingLeft":
        done.add(corpse.serial);
        return {};
      case "notCarvable":
        done.add(corpse.serial);
        emptied.add(corpse.serial);
        return {};
      // Already inside CARVE_RANGE, so the shard disagrees about the range rather than the script
      // having misjudged it
      case "tooFar":
        return setAside(corpse, "is out of reach");
      case "notSeen":
        return setAside(corpse, "is not in line of sight");
      default:
        return void 0;
    }
  };
  runHarvest({
    prefix: "carve",
    landed: "carved",
    toolName: "butcher knife",
    stopReason,
    isSaving,
    waitOutSave,
    equipTool: () => knifeSerial() !== void 0,
    relieve: () => {
      if (!LOOT_CORPSES) {
        return void 0;
      }
      const corpse = pending(inReach(onGround(), CARVE_RANGE));
      if (!corpse) {
        return void 0;
      }
      const took = take(corpse, packSerial);
      if (took.items > 0) {
        taken += took.items;
        log(`carve: took ${took.items} from ${hex(corpse.serial)}, ${taken} in total`);
      }
      return { phase: "looting" };
    },
    approach: () => {
      const all = onGround();
      const corpse = nextToCarve(inReach(all, CARVE_RANGE));
      if (corpse) {
        saidOutOfReach = false;
        return { target: corpse };
      }
      const closest = nearest(all);
      if (closest !== void 0 && !saidOutOfReach) {
        saidOutOfReach = true;
        log(
          `carve: ${all.length} corpses about, nearest ${closest} tiles away - nothing within ${CARVE_RANGE} left to carve`
        );
      }
      if (++waits % PRUNE_EVERY === 0) {
        prune();
      }
      heartbeat.beat("watching", waits, carved);
      sleep(WATCH_POLL);
      return { waited: true };
    },
    harvest: (corpse) => {
      const knife2 = knifeSerial();
      if (!corpse || knife2 === void 0) {
        return void 0;
      }
      const outcome = carveOnce(corpse, knife2);
      if (outcome === "carved") {
        carved++;
        memory().done.add(corpse.serial);
      }
      return outcome;
    },
    handle,
    progress: (tally) => `${tally} carved, ${taken} taken`,
    finish: (tally) => log(`carve: ${tally} corpses carved, ${taken} items taken`),
    stall: createStallWatch({
      prefix: "carve",
      without: "cycles without a carve landing",
      warnAt: STALL_WARN,
      stopAt: STALL_STOP,
      heartbeat
    }),
    timings: {
      stepDelay: STEP_DELAY,
      maxCycles: MAX_CYCLES,
      maxUnknown: MAX_UNKNOWN,
      maxThrottled: MAX_THROTTLED,
      maxNoCursor: MAX_NO_CURSOR,
      maxNoTool: MAX_NO_TOOL,
      logEvery: LOG_EVERY,
      throttleBackoff: THROTTLE_BACKOFF,
      throttleBackoffMax: THROTTLE_BACKOFF_MAX
    }
  });
})();
