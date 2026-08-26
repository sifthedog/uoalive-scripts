"use strict";
(() => {
  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var minutes = (ms) => Math.max(1, Math.round(ms / 6e4));
  var minutesLeft = (until) => minutes(until - now());
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);
  var createIdleWait = (options) => {
    return (until) => {
      const wait = until - now();
      if (wait <= 0) {
        return;
      }
      log(`${options.prefix}: ${options.waitingFor}, waiting ${minutesLeft(until)}m`);
      const slices = Math.ceil(wait / options.pollMs);
      let since = 0;
      for (let slice = 0; slice < slices && now() < until; slice++) {
        sleep(options.pollMs);
        since += options.pollMs;
        options.watch?.();
        if (options.stopReason()) {
          return;
        }
        if (since >= options.logEveryMs) {
          since = 0;
          log(`${options.prefix}: ${minutesLeft(until)}m to go`);
        }
      }
      options.onDone();
    };
  };
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
    landed,
    toolName,
    stopReason: stopReason2,
    watch,
    equipTool,
    ready,
    relieve,
    approach: approach2,
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
    let reported2 = 0;
    let throttled = 0;
    let noCursor = 0;
    const endCycle = (phase, cycle) => {
      stall.endCycle(phase, cycle, tally);
      stop ?? (stop = stall.reason());
    };
    for (let cycle = 0; cycle < timings.maxCycles && !stop; cycle++) {
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
        stop = `no ${toolName}`;
        break;
      }
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
      if (approach2) {
        const found = approach2();
        if ("stop" in found) {
          stop = found.stop;
          break;
        }
        if ("waited" in found) {
          continue;
        }
        if ("walked" in found) {
          endCycle("walking", cycle);
          continue;
        }
        target2 = found.target;
      }
      const outcome = harvest(target2);
      if (outcome === landed) {
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
      if (tally >= reported2 + timings.logEvery) {
        reported2 = tally;
        log(`${prefix}: ${progress(tally)}, ${player.weight}/${player.weightMax}`);
      }
      endCycle(outcome ?? "unknown", cycle);
      sleep(timings.stepDelay);
    }
    const reason = stop ?? `hit the ${timings.maxCycles} cycle backstop`;
    finish?.(tally, reason);
    log(`${prefix}: stopping - ${reason}`);
    exit(`${prefix}: ${reason}`);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var distanceTo = (spot) => Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));
  var isMobile = (entity) => entity._tag === "Mobile";
  var nameOf = (entity) => entity.name || hex(entity.serial);
  var describeItem = (item) => item ? `${hex(item.graphic)} '${item.name ?? ""}'` : "empty";
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

  // src/lib/tiles.ts
  var tileKey = (tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;
  var minutes2 = (ms) => Math.max(1, Math.round(ms / 6e4));
  var createTileStore = (options) => {
    const block = (tile, until) => options.blocked().set(tileKey(tile), until);
    return {
      block,
      blockedUntil: (tile) => options.blocked().get(tileKey(tile)),
      markDepleted: (tile) => {
        block(tile, now() + options.depletedFor);
        log(
          `${options.label}: ${tile.x},${tile.y} ${options.depleted}, back in ${minutes2(options.depletedFor)}m`
        );
      },
      markUnreachable: (tile) => {
        block(tile, now() + options.unreachableFor);
        log(
          `${options.label}: ${tile.x},${tile.y} could not be walked to, retrying in ${minutes2(options.unreachableFor)}m`
        );
      },
      markUnusable: (tile, reason) => {
        block(tile, Infinity);
        log(`${options.label}: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
      }
    };
  };
  var withinZOf = (z, allowed) => Math.abs(z - player.z) <= allowed;
  var createScan = (options) => {
    const reported2 = /* @__PURE__ */ new Set();
    return (radius = options.radius) => {
      const blocked = options.blocked();
      const time = now();
      let best;
      let readyAt;
      for (let dx = -radius; dx <= radius; dx++) {
        for (let dy = -radius; dy <= radius; dy++) {
          for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
            if (options.skipLand && tile.isLand) {
              continue;
            }
            if (options.withinZ !== void 0 && !withinZOf(tile.z, options.withinZ)) {
              continue;
            }
            if (!options.matches(tile.graphic, tile.isLand)) {
              continue;
            }
            if (options.reachable && !options.reachable(tile.x, tile.y)) {
              continue;
            }
            const candidate = {
              x: tile.x,
              y: tile.y,
              z: tile.z,
              graphic: tile.graphic,
              isLand: tile.isLand,
              distance: distanceTo(tile)
            };
            const key = tileKey(candidate);
            const until = blocked.get(key);
            if (until !== void 0) {
              if (time < until) {
                if (Number.isFinite(until) && (readyAt === void 0 || until < readyAt)) {
                  readyAt = until;
                }
                continue;
              }
              blocked.delete(key);
            }
            if (!best || candidate.distance < best.distance) {
              best = candidate;
            }
          }
        }
      }
      if (best && !reported2.has(best.graphic)) {
        log(`${options.label}: matching ${hex(best.graphic)} ${options.describe(best)}`);
        reported2.add(best.graphic);
      }
      return { found: best, readyAt };
    };
  };
  var createApproach = (options) => {
    let walkingTo;
    let steps = 0;
    return () => {
      const { found, readyAt } = options.scan();
      if (!found) {
        if (readyAt === void 0) {
          return { stop: options.nothingFound() };
        }
        options.idleUntil(readyAt);
        return { waited: true };
      }
      if (found.distance <= options.range) {
        walkingTo = void 0;
        return { target: found };
      }
      const key = `${found.x},${found.y}`;
      if (key !== walkingTo) {
        walkingTo = key;
        steps = 0;
      }
      if (!options.step(found) && !options.isSaving?.() || ++steps > options.maxSteps) {
        options.markUnreachable(found);
        walkingTo = void 0;
      }
      return { walked: true };
    };
  };

  // src/lib/weight.ts
  var overweight = (buffer = 0) => player.weightMax > 0 && player.weight > player.weightMax - buffer;

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
  var findIn = (contents, matches2) => {
    for (const item of contents ?? []) {
      if (matches2(item)) {
        return item;
      }
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        const foundInSub = findIn(sub, matches2);
        if (foundInSub) return foundInSub;
      }
    }
    return null;
  };
  var collectIn = (contents, matches2) => {
    const found = [];
    for (const item of contents ?? []) {
      if (matches2(item)) {
        found.push(item);
      }
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        found.push(...collectIn(sub, matches2));
      }
    }
    return found;
  };

  // src/lib/retry.ts
  var untilLanded = (options) => {
    for (let attempt = 1; attempt <= options.attempts; attempt++) {
      options.act();
      for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (options.landed()) {
          return true;
        }
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

  // src/lib/timings.ts
  var SCAN_RADIUS = 12;
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var IDLE_POLL = 1e4;
  var IDLE_LOG_EVERY = 6e4;
  var STEP_DELAY = 300;
  var WALK_DELAY = 300;
  var TARGET_TIMEOUT = 2e3;
  var EQUIP_TIMEOUT = 2e3;
  var EQUIP_POLL = 200;
  var EQUIP_ATTEMPTS = 3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var STALL_WARN = 60;
  var STALL_STOP = 300;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var MAX_UNKNOWN = 5;
  var MAX_NO_CURSOR = 20;
  var NO_CURSOR_READ = 500;
  var MAX_STEPS = 20;
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
  var UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill"
  ];
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;
  var THREAT_RANGE = 12;
  var WATCH_FOR_TROUBLE = true;
  var GUARD_CALL = "guards";
  var GUARD_CALLS = 3;
  var GUARD_CALL_DELAY = 1e4;
  var GUARD_REPLY_WAIT = 800;
  var NO_GUARDS_TEXT = [
    "The guards can not be called here",
    "The guards cannot be called here",
    "Guards can not be called here",
    "Guards cannot be called here",
    "There are no guards here"
  ];
  var ATTACK_TEXT = [];
  var GUARD_ZONE_TEXT = ["under the protection of the town guards", "now under guard"];
  var UNGUARDED_TEXT = ["left the protection of the town guards", "no longer under guard"];

  // src/lumberjacking/config.ts
  var AXE_NAME = "axe";
  var SPARE_BAG_SERIAL = void 0;
  var TREE_GRAPHICS = /* @__PURE__ */ new Set();
  var NOT_TREE_GRAPHICS = /* @__PURE__ */ new Set();
  var BOUNDS = { minX: 2400, maxX: 2580, minY: 400, maxY: 600 };
  var CHOP_RANGE = 2;
  var LOG_GRAPHICS = /* @__PURE__ */ new Set([7133, 7136, 7134, 7135]);
  var BOARD_GRAPHICS = /* @__PURE__ */ new Set([7127, 7129, 7130, 7131]);
  var REGROW_DELAY = 25 * 60 * 1e3;
  var CHOP_TIMEOUT = 8e3;
  var CHOP_TARGET_TIMEOUT = 4e3;
  var CHOP_TARGET_POLL = 100;
  var CHOP_PROMPT_TEXT = [
    "What do you want to use this on",
    "Select a tree",
    "Where do you wish to chop"
  ];
  var PACK_ANIMAL_SERIALS = [];
  var PACK_ANIMAL_GRAPHICS = /* @__PURE__ */ new Set([291, 292, 791]);
  var PICK_PACK_ANIMALS = true;
  var MAX_PICKS = 8;
  var OPL_TIMEOUT = 2e3;
  var UNLOAD_RANGE = 2;
  var HAUL_BUFFER = 120;
  var CONVERT_DELAY = 700;
  var MOVE_DELAY = 700;
  var CONVERT_TIMEOUT = 4e3;
  var CONVERT_POLL = 200;
  var CONVERT_ATTEMPTS = 3;
  var MAX_CONVERT_PASSES = 60;
  var WEIGHT_BUFFER = 40;
  var OUTCOME_TEXT = {
    chopped: ["You put", "You hack at the tree", "You chop some"],
    empty: ["There's not enough wood here to harvest", "There are no logs left"],
    // "You can't use an axe on that" is UOAlive's wording, seen on a live run against an 'o'hii tree'
    // static (0xc9e) - the tiledata calls it a tree, the shard will not harvest it
    notTree: [
      "You can't use an axe on that",
      "You can't chop that",
      "You can't use a bladed item on that",
      "You cannot chop"
    ],
    tooFar: ["That is too far away", "You cannot reach that"],
    // Confirmed from a live run. Line of sight, not range: the tile is inside CHOP_RANGE and no amount
    // of walking closer or waiting fixes it.
    notSeen: ["Target cannot be seen"],
    wornOut: ["You have worn out your tool"],
    // Without a bucket of its own a world save reads as five unreadable outcomes in a row, which ended
    // a live mining run.
    saving: SAVING_TEXT,
    // Full wordings first: the bare prefix also catches "You must wait N seconds" from systems that
    // have nothing to do with harvesting. Kept last as a fallback all the same - a phrase this list
    // misses reads as an unreadable outcome, which is worse.
    throttled: ["You must wait to perform another action", "You must wait a moment", "You must wait"]
  };

  // src/lumberjacking/axe.ts
  var axe = /* @__PURE__ */ createTool({
    label: "axe",
    name: AXE_NAME,
    spareBagSerial: SPARE_BAG_SERIAL,
    // Axes are two-handed, hatchets are one-handed, and either will chop
    held: () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL }
  });
  var isAxe = axe.is;
  var rememberAxe = axe.remember;
  var axeSerial = axe.serial;
  var equipAxe = axe.equip;

  // src/lib/pack.ts
  var countsByGraphic = (contents = packContents()) => {
    const counts = /* @__PURE__ */ new Map();
    const walk = (items) => {
      for (const item of items ?? []) {
        const key = `0x${item.graphic.toString(16)}/${item.hue ?? 0}`;
        counts.set(key, (counts.get(key) ?? 0) + (item.amount ?? 1));
        walk(contentsOf(item));
      }
    };
    walk(contents);
    return counts;
  };
  var diffCounts = (before, after) => {
    const changes = [];
    for (const [key, total] of after) {
      const delta = total - (before.get(key) ?? 0);
      if (delta !== 0) {
        changes.push({ key, delta });
      }
    }
    for (const [key, total] of before) {
      if (!after.has(key)) {
        changes.push({ key, delta: -total });
      }
    }
    return changes;
  };
  var totalMatching = (matches2, contents = packContents()) => (contents ?? []).reduce(
    (total, item) => total + (matches2(item) ? item.amount ?? 1 : 0) + totalMatching(matches2, contentsOf(item) ?? []),
    0
  );

  // src/lib/convert.ts
  var createConverter = (options) => {
    const writtenOff = /* @__PURE__ */ new Set();
    const misses = /* @__PURE__ */ new Map();
    let progressed = true;
    const missed = (hue) => {
      const count = (misses.get(hue) ?? 0) + 1;
      misses.set(hue, count);
      if (count >= options.attempts) {
        writtenOff.add(hue);
        log(`${options.label}: hue ${hue} failed ${count} times, ${options.leftAs}`);
      }
    };
    const learnOutput = (changes) => {
      for (const { key, delta } of changes) {
        if (delta <= 0) {
          continue;
        }
        const graphic = Number(key.split("/")[0]);
        if (options.known().some((set) => set.has(graphic))) {
          continue;
        }
        options.learn(graphic);
        log(`${options.label}: ${options.learned} is ${hex(graphic)}`);
      }
    };
    const waitForChange = (before) => {
      for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
        sleep(options.pollMs);
        const changes = diffCounts(before, countsByGraphic());
        if (changes.length > 0) {
          return changes;
        }
      }
      return [];
    };
    const saving = (hue) => {
      if (!options.isSaving()) {
        return false;
      }
      log(`${options.label}: the world is saving, not counting it against hue ${hue}`);
      return true;
    };
    const convertOne = (stack) => {
      const hue = stack.hue ?? 0;
      const before = countsByGraphic();
      if (!options.perform(stack)) {
        if (saving(hue)) {
          return;
        }
        missed(hue);
        return;
      }
      const changes = waitForChange(before);
      if (changes.length > 0) {
        misses.delete(hue);
        progressed = true;
        learnOutput(changes);
        return;
      }
      if (saving(hue)) {
        return;
      }
      if (options.throttledText?.some((text) => journal.containsText(text))) {
        log(`${options.label}: the shard says wait, not counting it against hue ${hue}`);
        return;
      }
      if (options.unskilledText.some((text) => journal.containsText(text))) {
        writtenOff.add(hue);
        log(`${options.label}: not skilled enough for hue ${hue}, ${options.leftAs}`);
        return;
      }
      missed(hue);
    };
    return {
      writtenOff,
      run: () => {
        for (let pass = 0; pass < options.maxPasses; pass++) {
          if (options.isSaving()) {
            log(`${options.label}: the world is saving, leaving it for now`);
            return false;
          }
          const stack = options.nextStack(writtenOff);
          if (!stack) {
            const skipped = options.describeSkipped?.(writtenOff);
            if (skipped) {
              log(`${options.label}: ${skipped}`);
            }
            return true;
          }
          const blocked = options.notNow?.();
          if (blocked) {
            log(`${options.label}: ${blocked}, leaving it for now`);
            return false;
          }
          convertOne(stack);
          sleep(options.delayMs);
        }
        log(`${options.label}: hit the ${options.maxPasses} pass backstop`);
        return false;
      },
      retry: () => {
        if (writtenOff.size === 0 || !progressed) {
          return false;
        }
        progressed = false;
        log(`${options.label}: giving ${writtenOff.size} hue(s) written off earlier another go`);
        writtenOff.clear();
        misses.clear();
        return true;
      }
    };
  };

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/lumberjacking/chop.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var isLog = (item) => LOG_GRAPHICS.has(item.graphic);
  var logTotal = (contents) => totalMatching(isLog, contents);
  var silentOutcome = (serial, logsBefore) => {
    if (serial !== void 0 && !client.findObject(serial)) {
      return "wornOut";
    }
    if (logTotal() > logsBefore) {
      return "chopped";
    }
    return "unknown";
  };
  var refusedOutcome = (serial, logsBefore) => {
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, NO_CURSOR_READ);
    if (matched) {
      return outcomeFor(matched);
    }
    const silent = silentOutcome(serial, logsBefore);
    if (silent !== "unknown") {
      return silent;
    }
    log(
      `chopOnce: no target cursor - hand ${describeItem(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded)}, neither target.open nor CHOP_PROMPT_TEXT in ${CHOP_TARGET_TIMEOUT}ms`
    );
    return "noCursor";
  };
  var cursorOpened = () => {
    for (let waited = 0; waited < CHOP_TARGET_TIMEOUT; waited += CHOP_TARGET_POLL) {
      if (target.open || CHOP_PROMPT_TEXT.some((text) => journal.containsText(text))) {
        return true;
      }
      sleep(CHOP_TARGET_POLL);
    }
    return false;
  };
  var chopOnce = (tree, serial) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    const logsBefore = logTotal();
    journal.clear();
    player.useItemInHand();
    if (!cursorOpened()) {
      target.cancel();
      return refusedOutcome(serial, logsBefore);
    }
    target.terrain(tree.x, tree.y, tree.z, tree.graphic);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CHOP_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(serial, logsBefore);
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

  // src/lib/vitals.ts
  var hitsCeiling = () => player.maxHits > 0 ? player.maxHits : void 0;

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

  // src/lumberjacking/bounds.ts
  var describeBounds = () => BOUNDS ? `(${BOUNDS.minX},${BOUNDS.minY})-(${BOUNDS.maxX},${BOUNDS.maxY})` : "anywhere";
  var inBounds = (x, y) => !BOUNDS || x >= BOUNDS.minX && x <= BOUNDS.maxX && y >= BOUNDS.minY && y <= BOUNDS.maxY;
  var clamp = (value, low, high) => Math.min(Math.max(value, low), high);
  var reachableFromBounds = (x, y, range) => {
    if (!BOUNDS) {
      return true;
    }
    const standX = clamp(x, BOUNDS.minX, BOUNDS.maxX);
    const standY = clamp(y, BOUNDS.minY, BOUNDS.maxY);
    return Math.max(Math.abs(x - standX), Math.abs(y - standY)) <= range;
  };
  var allowedStep = (dx, dy) => {
    const options = [
      [dx, dy],
      [dx, 0],
      [0, dy]
    ];
    for (const [stepX, stepY] of options) {
      if (stepX === 0 && stepY === 0) {
        continue;
      }
      if (inBounds(player.x + stepX, player.y + stepY)) {
        return [stepX, stepY];
      }
    }
    return void 0;
  };

  // src/lumberjacking/guards.ts
  var insideBounds = () => inBounds(player.x, player.y) ? void 0 : `at ${player.x},${player.y}, outside ${describeBounds()}`;
  var stopReason = () => firstReason(dead, insideBounds, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));

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

  // src/lumberjacking/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "lumberjack",
    noun: "chops",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lumberjacking/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/lumberjacking/boards.ts
  var isBoard = (item) => BOARD_GRAPHICS.has(item.graphic);
  var converter = /* @__PURE__ */ createConverter({
    label: "makeBoards",
    leftAs: "leaving it as logs",
    attempts: CONVERT_ATTEMPTS,
    timeoutMs: CONVERT_TIMEOUT,
    pollMs: CONVERT_POLL,
    delayMs: CONVERT_DELAY,
    maxPasses: MAX_CONVERT_PASSES,
    unskilledText: UNSKILLED_TEXT,
    // Without it a throttled conversion reads as a verdict on the wood, and three busy moments write
    // hue 0 off - which is every ordinary log. smelt.ts has always passed it; this did not.
    throttledText: THROTTLED_TEXT,
    isSaving,
    nextStack: (writtenOff) => collectIn(packContents(), isLog).find((item) => !writtenOff.has(item.hue ?? 0)),
    // The tool is used and the resource targeted - the inverse of smelting
    perform: (stack) => {
      if (target.open) {
        target.cancel();
      }
      journal.clear();
      player.useItemInHand();
      if (!target.waitTargetEntity(stack.serial, TARGET_TIMEOUT)) {
        target.cancel();
        log("makeBoards: no target cursor, nothing usable in hand?");
        return false;
      }
      return true;
    },
    known: () => [LOG_GRAPHICS, BOARD_GRAPHICS],
    learn: (graphic) => BOARD_GRAPHICS.add(graphic),
    learned: "board graphic"
  });
  var unconvertible = converter.writtenOff;
  var makeBoards = converter.run;
  var retryUnconvertible = converter.retry;

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
  var describe2 = (info, oplTimeout, prefix) => {
    const serial = info.serial ?? 0;
    const found = client.findObject(serial);
    return {
      serial,
      name: resolveName(serial, oplTimeout, prefix),
      graphic: info.graphic ?? found?.graphic ?? 0,
      hue: info.hue ?? found?.hue ?? 0
    };
  };
  var pickMany = ({
    prefix,
    prompt,
    maxPicks,
    oplTimeout,
    keyOf,
    label
  }) => {
    const picks = [];
    const seen = /* @__PURE__ */ new Set();
    const name = label ?? ((picked) => picked.name);
    log(`${prefix}: ${prompt}`);
    let asked = 0;
    for (; asked < maxPicks; asked++) {
      const info = clicked(prefix);
      if (!info) {
        break;
      }
      const picked = describe2(info, oplTimeout, prefix);
      const key = keyOf(picked);
      if (key === void 0) {
        continue;
      }
      if (seen.has(key)) {
        log(`${prefix}: '${name(picked)}' is already on the list`);
        continue;
      }
      seen.add(key);
      picks.push(picked);
      log(`${prefix}:   ${picks.length}. ${name(picked)}`);
    }
    if (asked === maxPicks) {
      log(`${prefix}: ${maxPicks} clicks is as many as one run takes`);
      target.cancel();
    }
    return picks;
  };

  // src/lib/walk.ts
  var DIRECTION_BY_STEP = /* @__PURE__ */ new Map([
    ["0,-1", Directions.North],
    ["1,-1", Directions.Right],
    ["1,0", Directions.East],
    ["1,1", Directions.Down],
    ["0,1", Directions.South],
    ["-1,1", Directions.Left],
    ["-1,0", Directions.West],
    ["-1,-1", Directions.Up]
  ]);
  var createStepToward = (options) => {
    return (spot) => {
      const wantX = Math.sign(spot.x - player.x);
      const wantY = Math.sign(spot.y - player.y);
      const step = options.constrain ? options.constrain(wantX, wantY) : wantX === 0 && wantY === 0 ? void 0 : [wantX, wantY];
      if (step === void 0) {
        return false;
      }
      const direction = DIRECTION_BY_STEP.get(`${step[0]},${step[1]}`);
      if (direction === void 0) {
        return false;
      }
      const beforeX = player.x;
      const beforeY = player.y;
      player.run(direction);
      sleep(options.delayMs);
      player.run(direction);
      sleep(options.delayMs);
      return player.x !== beforeX || player.y !== beforeY;
    };
  };

  // src/lumberjacking/walk.ts
  var stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY, constrain: allowedStep });

  // src/lumberjacking/haul.ts
  var isCargo = (item) => isBoard(item) || isLog(item) && unconvertible.has(item.hue ?? 0);
  var writtenOffLogs = () => collectIn(packContents(), (item) => isLog(item) && unconvertible.has(item.hue ?? 0));
  var reported = false;
  var pinnedSerials = [...PACK_ANIMAL_SERIALS];
  var pickPackAnimals = () => {
    const resolved = /* @__PURE__ */ new Map();
    if (player.equippedItems.mount) {
      log("haul: you are mounted - dismount first if the animal you want is the one you are riding");
    }
    const picks = pickMany({
      prefix: "haul",
      prompt: "target the pack animals to load, ESC when done",
      maxPicks: MAX_PICKS,
      oplTimeout: OPL_TIMEOUT,
      // undefined skips the click without ending the selection, which is what a misclick on the
      // ground should cost
      keyOf: (click) => {
        const found = client.findObject(click.serial);
        if (!found || !isMobile(found)) {
          log(`haul: ${hex(click.serial)} is not a mobile`);
          return void 0;
        }
        if (!PACK_ANIMAL_GRAPHICS.has(found.graphic)) {
          log(`haul: ${hex(found.graphic)} is not a body PACK_ANIMAL_GRAPHICS knows, using it anyway`);
        }
        resolved.set(found.serial, found);
        return String(found.serial);
      }
    });
    const picked = picks.map((pick) => resolved.get(pick.serial)).filter((animal) => animal !== void 0);
    if (picked.length === 0) {
      log("haul: nothing picked, looking for the animals instead");
      return [];
    }
    pinnedSerials = picked.map((animal) => animal.serial);
    return picked;
  };
  var findPackAnimals = () => {
    if (pinnedSerials.length > 0) {
      return pinnedSerials.map((serial) => client.findObject(serial)).filter((pinned) => pinned !== void 0 && isMobile(pinned)).sort((a, b) => distanceTo(a) - distanceTo(b));
    }
    const found = [];
    for (const graphic of PACK_ANIMAL_GRAPHICS) {
      found.push(...client.findAllMobilesOfType(graphic, null, null, null, SCAN_RADIUS));
    }
    if (found.length === 0) {
      return [];
    }
    const mine = found.filter((animal) => animal.isRenamable);
    const candidates = mine.length ? mine : found;
    if (!reported) {
      const names = candidates.map((animal) => `'${animal.name ?? "?"}'`).join(", ");
      log(`haul: ${candidates.length} pack animal(s) - ${names}`);
      reported = true;
    }
    return candidates.sort((a, b) => distanceTo(a) - distanceTo(b));
  };
  var animalPack = (animal) => {
    const pack = client.findItemOnLayer(animal.serial, Layers.Backpack);
    if (pack) {
      return pack;
    }
    player.use(animal.serial);
    sleep(800);
    return client.findItemOnLayer(animal.serial, Layers.Backpack);
  };
  var walkToAnimal = (serial) => approach(serial, {
    label: "haul",
    range: UNLOAD_RANGE,
    maxSteps: MAX_STEPS,
    step: stepToward,
    isSaving
  }) !== void 0;
  var moveAll = (packSerial, matches2) => {
    let previousStacks = Infinity;
    while (true) {
      const stacks = collectIn(packContents(), matches2);
      if (stacks.length === 0 || stacks.length >= previousStacks) {
        return;
      }
      previousStacks = stacks.length;
      for (const stack of stacks) {
        player.moveItem(stack.serial, packSerial);
        sleep(MOVE_DELAY);
      }
    }
  };
  var unloadTo = (animals, matches2) => {
    let moved = false;
    for (const animal of animals) {
      const before = collectIn(packContents(), matches2).length;
      if (before === 0) {
        break;
      }
      if (!walkToAnimal(animal.serial)) {
        continue;
      }
      const pack = animalPack(animal);
      if (!pack) {
        log(`haul: '${nameOf(animal)}' has no reachable backpack`);
        continue;
      }
      moveAll(pack.serial, matches2);
      const after = collectIn(packContents(), matches2).length;
      if (after < before) {
        moved = true;
      }
      if (after > 0) {
        log(`haul: '${nameOf(animal)}' took ${before - after} of ${before} stacks, trying the next`);
      }
    }
    return moved;
  };
  var unload = () => {
    const animals = findPackAnimals();
    if (animals.length === 0) {
      log("haul: no pack animal nearby");
      return false;
    }
    if (writtenOffLogs().length > 0 && retryUnconvertible()) {
      makeBoards();
    }
    const moved = unloadTo(animals, isCargo);
    if (overweight(HAUL_BUFFER)) {
      const logs = collectIn(packContents(), isLog);
      if (logs.length > 0) {
        retryUnconvertible();
        makeBoards();
        if (collectIn(packContents(), isLog).length === 0) {
          return unloadTo(animals, isCargo) || moved;
        }
        if (isSaving()) {
          log("haul: the world is saving, keeping the logs for the next haul");
          return moved;
        }
        const total = logs.reduce((sum, item) => sum + (item.amount ?? 1), 0);
        log(`haul: ${total} logs would not convert in time, moving them as logs`);
        return unloadTo(animals, isLog) || moved;
      }
    }
    return moved;
  };

  // src/lib/threat.ts
  var NOTORIETY = [
    "unknown",
    "innocent",
    "ally",
    "gray",
    "criminal",
    "enemy",
    "murderer",
    "invulnerable"
  ];
  var NOTORIETY_BIT = [
    0,
    SearchEntityOptions.Innocent,
    SearchEntityOptions.Friend,
    SearchEntityOptions.Gray,
    SearchEntityOptions.Criminal,
    SearchEntityOptions.Enemy,
    SearchEntityOptions.Murderer,
    SearchEntityOptions.Invulnerable
  ];
  var matches = (mobile, mask) => ((NOTORIETY_BIT[mobile.notoriety] ?? 0) & mask) !== 0;
  var dropped = (was, is) => was > 0 && is > 0 && is < was;
  var createThreatWatch = (options) => {
    let lastHits = 0;
    let lastCompanionHits = 0;
    let lastCall = 0;
    let calls = 0;
    let episode = false;
    let noGuards = false;
    let saidProtection = false;
    let zone;
    const nearest = (mask, type) => {
      const found = client.selectEntity(mask, SearchEntityRangeOptions.Nearest, type, false);
      if (!found || found.serial === player.serial || found.isDead) {
        return void 0;
      }
      return distanceTo(found) <= options.range ? found : void 0;
    };
    const hostileNear = () => {
      const found = nearest(options.hostile, SearchEntityTypeOptions.Any);
      return found && !found.isRenamable ? found : void 0;
    };
    const readZone = () => {
      if (options.guardedText.some((text) => journal.containsText(text))) {
        zone = "guarded";
      } else if (options.unguardedText.some((text) => journal.containsText(text))) {
        zone = "unguarded";
      }
    };
    const protection = () => {
      if (zone) {
        return `the journal says ${zone}`;
      }
      const yellow = nearest(SearchEntityOptions.Invulnerable, SearchEntityTypeOptions.Human);
      return yellow ? `an invulnerable '${nameOf(yellow)}' in sight, so probably a town` : "nothing in sight to say either way";
    };
    const callGuards = () => {
      if (noGuards || options.calls > 0 && calls >= options.calls) {
        return;
      }
      const at = now();
      if (calls > 0 && at - lastCall < options.callDelay) {
        return;
      }
      lastCall = at;
      calls++;
      if (!saidProtection) {
        saidProtection = true;
        log(`${options.prefix}: guard protection - ${protection()}`);
      }
      log(
        `${options.prefix}: calling the guards (${calls}${options.calls > 0 ? `/${options.calls}` : ""})`
      );
      player.say(options.call);
      if (options.noGuardsText.length === 0) {
        return;
      }
      const refused = journal.waitForTextAny(options.noGuardsText, void 0, options.replyWait);
      if (refused) {
        noGuards = true;
        log(`${options.prefix}: the shard says '${refused}' - not calling again this run`);
      }
    };
    const describe3 = (hostile, friend) => {
      const who = hostile ? `'${nameOf(hostile)}' ${hex(hostile.graphic)} ${distanceTo(hostile)} tiles off (${NOTORIETY[hostile.notoriety] ?? hostile.notoriety})` : "nothing in sight";
      const mine = `you ${player.hits}/${hitsCeiling() ?? "?"}`;
      const theirs = friend ? `, ${options.companionName} ${friend.hits}/${friend.maxHits || "?"}` : "";
      return `${who}, ${mine}${theirs}`;
    };
    return {
      check: () => {
        readZone();
        const hits = player.hits;
        const hurt = dropped(lastHits, hits);
        if (hits > 0) {
          lastHits = hits;
        }
        const friend = options.companion?.();
        const friendHits = friend?.hits ?? 0;
        const friendHurt = dropped(lastCompanionHits, friendHits);
        if (friendHits > 0) {
          lastCompanionHits = friendHits;
        }
        const said = options.attackText.some((text) => journal.containsText(text));
        const hostile = hostileNear();
        if (!hostile && !hurt && !friendHurt && !said) {
          if (episode) {
            episode = false;
            calls = 0;
            log(`${options.prefix}: clear`);
          }
          return;
        }
        if (!episode) {
          episode = true;
          log(`${options.prefix}: trouble - ${describe3(hostile, friend)}`);
        }
        if (hurt || friendHurt || said || hostile && matches(hostile, options.callOnSight)) {
          callGuards();
        }
      }
    };
  };

  // src/lumberjacking/threat.ts
  var watchForTrouble = WATCH_FOR_TROUBLE ? createThreatWatch({
    prefix: "lumberjack",
    range: THREAT_RANGE,
    hostile: HOSTILE_NOTORIETY,
    callOnSight: CALL_ON_SIGHT_NOTORIETY,
    companion: () => findPackAnimals()[0],
    companionName: "pack animal",
    call: GUARD_CALL,
    calls: GUARD_CALLS,
    callDelay: GUARD_CALL_DELAY,
    replyWait: GUARD_REPLY_WAIT,
    noGuardsText: NO_GUARDS_TEXT,
    attackText: ATTACK_TEXT,
    guardedText: GUARD_ZONE_TEXT,
    unguardedText: UNGUARDED_TEXT
  }).check : void 0;

  // src/lib/store.ts
  var scope = globalThis;
  var createStore = (options) => {
    let held;
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
      read: () => held ?? (held = load()),
      // Tests only. vi.resetModules() gives each test a fresh module registry but leaves globalThis
      // alone, which is precisely what this store is designed to survive.
      forget: () => {
        delete scope[options.key];
        held = void 0;
      }
    };
  };

  // src/lumberjacking/memory.ts
  var KEY = "__lumberjack_memory";
  var VERSION = 1;
  var store = /* @__PURE__ */ createStore({
    key: KEY,
    version: VERSION,
    seed: () => ({ blocked: /* @__PURE__ */ new Map(), notTree: /* @__PURE__ */ new Set() }),
    describe: (found) => found.blocked.size > 0 || found.notTree.size > 0 ? `memory: resuming with ${found.blocked.size} blocked tiles, ${found.notTree.size} arts` : void 0
  });
  var memory = store.read;
  var forget = store.forget;

  // src/lumberjacking/tree.ts
  var known = /* @__PURE__ */ new Map();
  var isTree = (graphic) => {
    if (TREE_GRAPHICS.has(graphic)) {
      return true;
    }
    if (NOT_TREE_GRAPHICS.has(graphic) || memory().notTree.has(graphic)) {
      return false;
    }
    const remembered = known.get(graphic);
    if (remembered !== void 0) {
      return remembered;
    }
    const name = client.getStatic(graphic)?.name ?? "";
    const matches2 = /tree/i.test(name);
    known.set(graphic, matches2);
    return matches2;
  };
  var store2 = /* @__PURE__ */ createTileStore({
    label: "tree",
    blocked: () => memory().blocked,
    depletedFor: REGROW_DELAY,
    unreachableFor: UNREACHABLE_DELAY,
    depleted: "is out of wood"
  });
  var markDepleted = store2.markDepleted;
  var markUnreachable = store2.markUnreachable;
  var markUnusable = store2.markUnusable;
  var markNotHarvestable = (graphic) => {
    const { notTree } = memory();
    if (notTree.has(graphic)) {
      return;
    }
    notTree.add(graphic);
    log(`tree: ${hex(graphic)} cannot be chopped, skipping that art from here on`);
  };
  var scan = /* @__PURE__ */ createScan({
    label: "scanForTree",
    radius: SCAN_RADIUS,
    blocked: () => memory().blocked,
    // A tree is a static, so land is skipped outright rather than asked about
    skipLand: true,
    matches: (graphic) => isTree(graphic),
    // Trees outside the box are still fair game when a legal standing tile is within CHOP_RANGE;
    // filtered here rather than picked, walked at, refused and written off MAX_STEPS later.
    reachable: (x, y) => reachableFromBounds(x, y, CHOP_RANGE),
    describe: (tree) => `'${client.getStatic(tree.graphic)?.name ?? "?"}'`
  });
  var scanForTree = () => {
    const { found, readyAt } = scan();
    return { tree: found, regrowsAt: readyAt };
  };

  // src/lumberjacking/index.ts
  rememberAxe(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded);
  var idleUntil = createIdleWait({
    prefix: "lumberjack",
    waitingFor: "everything in reach is regrowing",
    pollMs: IDLE_POLL,
    logEveryMs: IDLE_LOG_EVERY,
    stopReason,
    watch: watchForTrouble,
    onDone: resetBeat
  });
  log(`lumberjack: ${logTotal()} logs in the pack to start, staying within ${describeBounds()}`);
  if (PICK_PACK_ANIMALS) {
    pickPackAnimals();
  }
  var hauling = true;
  var haulForRoom = () => {
    if (!hauling || !overweight(HAUL_BUFFER)) {
      return void 0;
    }
    makeBoards();
    const moved = unload();
    if (isSaving()) {
      waitOutSave();
    } else if (!moved) {
      hauling = false;
      log("lumberjack: hauling freed nothing, carrying on until overweight");
    }
    return { phase: "hauling" };
  };
  var handle = (outcome, tree) => {
    if (!tree) {
      return void 0;
    }
    switch (outcome) {
      // A stump, not a dead tile: markDepleted times it out and the scan picks it up again later
      case "empty":
        markDepleted(tree);
        return {};
      // The whole art is scenery, not just this tile, so ban the graphic rather than walking to the
      // forest's copies of it one at a time
      case "notTree":
        markNotHarvestable(tree.graphic);
        markUnusable(tree, "is not harvestable");
        return {};
      // Already inside CHOP_RANGE, so the shard disagrees about the range rather than the walk having
      // fallen short
      case "tooFar":
        markUnusable(tree, `is out of reach at ${tree.distance} tiles`);
        return {};
      // Line of sight: walking closer would not help and neither would waiting. Without this the tile
      // reads as an unreadable outcome, is picked again by the next scan, and five end the run.
      case "notSeen":
        markUnusable(tree, "is not in line of sight");
        return {};
      default:
        return void 0;
    }
  };
  runHarvest({
    prefix: "lumberjack",
    landed: "chopped",
    toolName: "axe",
    stopReason,
    watch: watchForTrouble,
    equipTool: equipAxe,
    relieve: haulForRoom,
    isSaving,
    waitOutSave,
    approach: createApproach({
      // Renamed rather than shared: 'tree' and 'regrowsAt' are what this folder's tests read
      scan: () => {
        const { tree, regrowsAt } = scanForTree();
        return { found: tree, readyAt: regrowsAt };
      },
      range: CHOP_RANGE,
      maxSteps: MAX_STEPS,
      step: stepToward,
      markUnreachable,
      idleUntil,
      isSaving,
      nothingFound: () => "no tree in range"
    }),
    harvest: (tree) => tree ? chopOnce(tree, axeSerial()) : void 0,
    handle,
    progress: (chopped) => `${chopped} chops, ${logTotal()} logs`,
    finish: (chopped) => {
      makeBoards();
      if (hauling) {
        unload();
      }
      log(`lumberjack: ${chopped} chops, ${logTotal()} logs still in the pack`);
    },
    stall: createStallWatch({
      prefix: "lumberjack",
      without: "cycles without a chop",
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
      logEvery: LOG_EVERY,
      throttleBackoff: THROTTLE_BACKOFF,
      throttleBackoffMax: THROTTLE_BACKOFF_MAX
    }
  });
})();
