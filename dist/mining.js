"use strict";
(() => {
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
    watch: watch2,
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
      watch2?.();
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

  // src/lib/arts.ts
  var INGOT_GRAPHICS = /* @__PURE__ */ new Set([7151, 7152, 7153, 7154]);

  // src/mining/config.ts
  var PICKAXE_NAME = "pickaxe";
  var SPARE_BAG_SERIAL = void 0;
  var range = (from, to) => Array.from({ length: to - from + 1 }, (_, offset) => from + offset);
  var ORE_TILE_GRAPHICS = /* @__PURE__ */ new Set([
    ...range(220, 251),
    ...range(1339, 1359),
    ...range(1361, 1383),
    ...range(1386, 1394)
  ]);
  var NOT_ORE_GRAPHICS = /* @__PURE__ */ new Set();
  var ORE_STATIC_NAME = /cave|rock|mountain|ore/i;
  var MINE_RANGE = 2;
  var RESPAWN_DELAY = 25 * 60 * 1e3;
  var DIG_TIMEOUT = 8e3;
  var DIG_TARGET_TIMEOUT = 4e3;
  var DIG_TARGET_POLL = 100;
  var DIG_PROMPT_TEXT = ["Where do you wish to dig"];
  var ORE_GRAPHICS = /* @__PURE__ */ new Set([6583, 6586, 6585, 6584]);
  var ORE_NAME = /\bore\b/i;
  var COMBINE_DELAY = 700;
  var COMBINE_TIMEOUT = 2e3;
  var COMBINE_POLL = 200;
  var MAX_COMBINE_ATTEMPTS = 12;
  var DIFFERENT_ORE_TEXT = ["You cannot combine ores of different metals"];
  var ORE_SETTLE_TIMEOUT = 1500;
  var ORE_SETTLE_POLL = 150;
  var FIRE_BEETLE_GRAPHICS = /* @__PURE__ */ new Set([169]);
  var FIRE_BEETLE_SERIAL = void 0;
  var PICK_BEETLE = true;
  var BEETLE_SCAN_RADIUS = 18;
  var SMELT_RANGE = 2;
  var MAX_BEETLE_STEPS = 24;
  var SMELT_DELAY = 700;
  var SMELT_TIMEOUT = 4e3;
  var SMELT_POLL = 200;
  var MIN_SMELT_AMOUNT = 2;
  var SMELT_ATTEMPTS = 3;
  var MAX_SMELT_PASSES = 60;
  var UNSKILLED_TEXT2 = [
    "You have no idea how to smelt this strange ore",
    ...UNSKILLED_TEXT
  ];
  var DISMOUNT_TIMEOUT = 2e3;
  var DISMOUNT_POLL = 200;
  var DISMOUNT_ATTEMPTS = 3;
  var NOTHING_NEARBY_HINT = 5;
  var OUTCOME_TEXT = {
    dug: ["You dig some", "You put", "You loosen some rocks"],
    // Both wordings are in the wild: RunUO says metal, some shards say ore.
    empty: [
      "There is no metal here to mine",
      "There is no ore here to mine",
      "You cannot mine there"
    ],
    // Confirmed from a live run. Distinct from `empty` because of that last word: this is the shard
    // answering about everything within reach, so it parks the whole area and walks the character
    // away. Read as `empty` it would park one tile and get the same sentence back from the same spot.
    nothingNearby: [
      "There are no harvestable resources nearby",
      "There is nothing here to harvest"
    ],
    // About the art rather than the tile, so the whole graphic is banned
    notOre: ["You can't mine that", "Try mining in rock", "You can only mine"],
    tooFar: ["That is too far away", "You cannot reach that"],
    // Line of sight, not range: the tile is inside MINE_RANGE and no amount of walking closer or
    // waiting fixes it
    notSeen: ["Target cannot be seen"],
    // The ore is destroyed when this fires, not dropped, so it has to trigger a smelt rather than
    // another swing.
    packFull: ["Your backpack is full", "That container cannot hold more"],
    wornOut: ["You have worn out your tool"],
    // Without a bucket of its own a world save reads as five unreadable outcomes in a row, which ended
    // a live run.
    saving: SAVING_TEXT,
    // Shared with the smelt, which has no outcomes to read a refusal as: to the conversion a throttle
    // is silence, and silence is what writes a hue off. One list, so a correction fixes both.
    throttled: THROTTLED_TEXT
  };
  var SURVEY_ARTS = 15;

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

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
  var contentsOf = (item) => {
    try {
      return item?.contents;
    } catch (error) {
      const serial = item?.serial ?? 0;
      if (!unreadable.has(serial)) {
        unreadable.add(serial);
        log(`contents: ${hex(serial)} would not answer - ${String(error)}`);
      }
      return void 0;
    }
  };
  var packContents = () => {
    try {
      return contentsOf(player.backpack);
    } catch (error) {
      if (!unreadable.has(0)) {
        unreadable.add(0);
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
      return true;
    }
    let opened = false;
    for (const item of packContents() ?? []) {
      if (!isContainer(item)) {
        continue;
      }
      player.use(item.serial);
      sleep(800);
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

  // src/mining/ore.ts
  var isOrePile = (item) => {
    if (ORE_GRAPHICS.has(item.graphic)) {
      return true;
    }
    if (!ORE_NAME.test(item.name ?? "")) {
      return false;
    }
    ORE_GRAPHICS.add(item.graphic);
    log(`ore: 0x${item.graphic.toString(16)} '${item.name}' is ore too, remembering the art`);
    return true;
  };
  var oreTotal = (contents) => totalMatching(isOrePile, contents);
  var waitForOre = (before) => {
    for (let waited = 0; waited < ORE_SETTLE_TIMEOUT; waited += ORE_SETTLE_POLL) {
      if (oreTotal() > before) {
        return true;
      }
      sleep(ORE_SETTLE_POLL);
    }
    return false;
  };
  var amountOf = (item) => item.amount ?? 1;
  var hueOf = (item) => item.hue ?? 0;
  var describe = (item) => `${amountOf(item)} hue ${hueOf(item)}`;
  var orePiles = () => (packContents() ?? []).filter(isOrePile).sort((a, b) => amountOf(b) - amountOf(a));
  var differing = /* @__PURE__ */ new Set();
  var skipped = /* @__PURE__ */ new Set();
  var serialKey = (a, b) => a.serial < b.serial ? `s${a.serial}:${b.serial}` : `s${b.serial}:${a.serial}`;
  var hueKey = (a, b) => hueOf(a) < hueOf(b) ? `h${hueOf(a)}:${hueOf(b)}` : `h${hueOf(b)}:${hueOf(a)}`;
  var hueTellsThemApart = (a, b) => hueOf(a) !== 0 && hueOf(b) !== 0 && hueOf(a) !== hueOf(b);
  var differs = (a, b) => differing.has(serialKey(a, b)) || skipped.has(serialKey(a, b)) || hueTellsThemApart(a, b) && differing.has(hueKey(a, b));
  var said = (texts) => texts.some((text) => journal.containsText(text));
  var merged = (primary, dup, before) => {
    for (let waited = 0; waited < COMBINE_TIMEOUT; waited += COMBINE_POLL) {
      const piles = packContents() ?? [];
      const grown = piles.find((item) => item.serial === primary.serial);
      if (!piles.some((item) => item.serial === dup.serial) || grown && amountOf(grown) > before) {
        return true;
      }
      if (said(DIFFERENT_ORE_TEXT)) {
        return false;
      }
      sleep(COMBINE_POLL);
    }
    return false;
  };
  var combine = (primary, dup) => {
    const before = amountOf(primary);
    journal.clear();
    player.use(dup.serial);
    if (!target.waitTargetEntity(primary.serial, TARGET_TIMEOUT)) {
      target.cancel();
      skipped.add(serialKey(primary, dup));
      log(`groupOres: no target cursor for ${describe(dup)}`);
      return;
    }
    if (merged(primary, dup, before)) {
      return;
    }
    if (said(THROTTLED_TEXT)) {
      log("groupOres: the shard says wait, leaving the two of them paired");
      return;
    }
    if (said(DIFFERENT_ORE_TEXT)) {
      differing.add(serialKey(primary, dup));
      if (hueTellsThemApart(primary, dup)) {
        differing.add(hueKey(primary, dup));
      }
      return;
    }
    skipped.add(serialKey(primary, dup));
    log(`groupOres: ${describe(primary)} and ${describe(dup)} did not merge and nothing was said`);
  };
  var nextPair = (piles) => {
    const primaries = [];
    for (const pile of piles) {
      const home = primaries.find((primary) => hueOf(primary) === hueOf(pile) && !differs(primary, pile)) ?? primaries.find((primary) => !differs(primary, pile));
      if (home) {
        return [home, pile];
      }
      primaries.push(pile);
    }
    return void 0;
  };
  var groupOres = () => {
    skipped.clear();
    for (let attempt = 0; attempt < MAX_COMBINE_ATTEMPTS; attempt++) {
      const piles = orePiles();
      const pair = nextPair(piles);
      if (!pair) {
        if (skipped.size > 0 && piles.length > 1) {
          log(`groupOres: left ${piles.length} piles - ${piles.map(describe).join(", ")}`);
        }
        return;
      }
      combine(pair[0], pair[1]);
      sleep(COMBINE_DELAY);
    }
    log(`groupOres: hit the ${MAX_COMBINE_ATTEMPTS} attempt backstop`);
  };

  // src/mining/dig.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var silentOutcome = (serial, oreBefore2) => {
    if (serial !== void 0 && !client.findObject(serial)) {
      return "wornOut";
    }
    if (oreTotal() > oreBefore2) {
      return "dug";
    }
    return "unknown";
  };
  var refusedOutcome = (serial, oreBefore2) => {
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, NO_CURSOR_READ);
    if (matched) {
      return outcomeFor(matched);
    }
    const silent = silentOutcome(serial, oreBefore2);
    if (silent !== "unknown") {
      return silent;
    }
    log(
      `digOnce: no target cursor - hand ${describeItem(player.equippedItems.oneHanded)}, and the shard never asked where to dig`
    );
    return "noCursor";
  };
  var cursorOpened = () => {
    for (let waited = 0; waited < DIG_TARGET_TIMEOUT; waited += DIG_TARGET_POLL) {
      if (target.open || DIG_PROMPT_TEXT.some((text) => journal.containsText(text))) {
        return true;
      }
      sleep(DIG_TARGET_POLL);
    }
    return false;
  };
  var digOnce = (serial) => {
    target.clearQueue();
    if (target.open) {
      target.cancel();
    }
    const oreBefore2 = oreTotal();
    journal.clear();
    player.useItemInHand();
    if (!cursorOpened()) {
      return refusedOutcome(serial, oreBefore2);
    }
    target.self();
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, DIG_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(serial, oreBefore2);
  };

  // src/lib/vitals.ts
  var hitsCeiling = () => player.maxHits > 0 ? player.maxHits : void 0;

  // src/lib/weight.ts
  var overweight = (buffer = 0) => player.weightMax > 0 && player.weight > player.weightMax - buffer;

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
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

  // src/mining/guards.ts
  var stopReason = () => firstReason(dead, packFull(PACK_LIMIT));

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

  // src/mining/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "mining",
    noun: "swings",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

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

  // src/mining/mount.ts
  var reported = false;
  var dismount = () => {
    if (!player.equippedItems.mount) {
      return true;
    }
    if (!reported) {
      log("mount: getting off before working");
      reported = true;
    }
    target.cancel();
    const off = untilLanded({
      label: "dismount",
      attempts: DISMOUNT_ATTEMPTS,
      timeoutMs: DISMOUNT_TIMEOUT,
      pollMs: DISMOUNT_POLL,
      // Double-clicking yourself is how you get off; there is no dismount call in this API
      act: () => player.use(player.serial),
      // The mount layer clearing is the proof
      landed: () => !player.equippedItems.mount
    });
    if (off) {
      reported = false;
    }
    return off;
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

  // src/mining/pickaxe.ts
  var pickaxe = /* @__PURE__ */ createTool({
    label: "pickaxe",
    name: PICKAXE_NAME,
    spareBagSerial: SPARE_BAG_SERIAL,
    held: () => player.equippedItems.oneHanded,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL }
  });
  var isPickaxe = pickaxe.is;
  var rememberPickaxe = pickaxe.remember;
  var pickaxeSerial = pickaxe.serial;
  var equipPickaxe = pickaxe.equip;

  // src/lib/save.ts
  var createSaveWatch = (options) => ({
    isSaving: () => options.savingText.some((text) => journal.containsText(text)),
    waitOutSave: () => {
      log("save: the world is saving, waiting it out");
      journal.clear();
      for (let waited = 0; waited < options.waitMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (options.doneText.some((text) => journal.containsText(text))) {
          break;
        }
        if (options.stopReason()) {
          break;
        }
      }
      options.onDone();
    }
  });

  // src/mining/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

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
            const skipped2 = options.describeSkipped?.(writtenOff);
            if (skipped2) {
              log(`${options.label}: ${skipped2}`);
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

  // src/mining/walk.ts
  var stepToward = /* @__PURE__ */ createStepToward({ delayMs: WALK_DELAY });

  // src/mining/smelt.ts
  var beetleSerial = FIRE_BEETLE_SERIAL;
  var pinned = FIRE_BEETLE_SERIAL !== void 0;
  var reportedFound = false;
  var reportedMissing = false;
  var pickBeetle = () => {
    target.cancel();
    log("smelt: target your fire beetle, ESC to let the script find it");
    const serial = target.query()?.serial ?? 0;
    if (!serial) {
      target.cancel();
      log("smelt: nothing picked, looking for one instead");
      return void 0;
    }
    const picked = client.findObject(serial);
    if (!picked || !isMobile(picked)) {
      log(`smelt: ${hex(serial)} is not a mobile, looking for one instead`);
      return void 0;
    }
    if (!FIRE_BEETLE_GRAPHICS.has(picked.graphic)) {
      log(`smelt: ${hex(picked.graphic)} is not a body FIRE_BEETLE_GRAPHICS knows, using it anyway`);
    }
    beetleSerial = serial;
    pinned = true;
    reportedFound = true;
    log(`smelt: using '${nameOf(picked)}' ${hex(picked.graphic)} as the forge`);
    return picked;
  };
  var findBeetle = () => {
    if (beetleSerial !== void 0) {
      const resolved = client.findObject(beetleSerial);
      if (resolved && isMobile(resolved)) {
        return resolved;
      }
      if (pinned) {
        return void 0;
      }
      beetleSerial = void 0;
    }
    const found = [];
    for (const graphic of FIRE_BEETLE_GRAPHICS) {
      found.push(...client.findAllMobilesOfType(graphic, null, null, null, BEETLE_SCAN_RADIUS));
    }
    if (found.length === 0) {
      return void 0;
    }
    const mine = found.filter((beetle2) => beetle2.isRenamable);
    const candidates = mine.length ? mine : found;
    const beetle = candidates.sort((a, b) => distanceTo(a) - distanceTo(b))[0];
    if (!reportedFound) {
      log(`smelt: using '${nameOf(beetle)}' ${hex(beetle.graphic)} as the forge`);
      reportedFound = true;
    }
    beetleSerial = beetle.serial;
    return beetle;
  };
  var walkToBeetle = (serial) => approach(serial, {
    label: "smelt",
    range: SMELT_RANGE,
    maxSteps: MAX_BEETLE_STEPS,
    step: stepToward,
    isSaving
  });
  var bigEnough = (item) => {
    const amount = item.amount ?? 0;
    return amount === 0 || amount >= MIN_SMELT_AMOUNT;
  };
  var describePile = (item, writtenOff) => {
    const amount = item.amount ?? 0;
    const hue = item.hue ?? 0;
    if (writtenOff.has(hue)) {
      return `${amount} hue ${hue} (written off)`;
    }
    if (!bigEnough(item)) {
      return `${amount} hue ${hue} (too small)`;
    }
    return `${amount} hue ${hue}`;
  };
  var nextOre = (writtenOff) => collectIn(packContents(), isOrePile).find(
    (item) => !writtenOff.has(item.hue ?? 0) && bigEnough(item)
  );
  var forge;
  var forgeGone = () => {
    if (!forge) {
      return "no beetle to smelt against";
    }
    const here = client.findObject(forge.serial);
    if (!here || !isMobile(here)) {
      return `the beetle ${hex(forge.serial)} is out of sight`;
    }
    const away = distanceTo(here);
    return away > SMELT_RANGE ? `the beetle has wandered ${away} tiles off` : void 0;
  };
  var converter = /* @__PURE__ */ createConverter({
    label: "smelt",
    leftAs: "leaving it as ore",
    attempts: SMELT_ATTEMPTS,
    timeoutMs: SMELT_TIMEOUT,
    pollMs: SMELT_POLL,
    delayMs: SMELT_DELAY,
    maxPasses: MAX_SMELT_PASSES,
    unskilledText: UNSKILLED_TEXT2,
    throttledText: THROTTLED_TEXT,
    isSaving,
    notNow: forgeGone,
    nextStack: (writtenOff) => nextOre(writtenOff),
    describeSkipped: (writtenOff) => {
      const piles = collectIn(packContents(), isOrePile);
      return piles.length > 0 ? `nothing to smelt in ${piles.length} pile(s) - ` + piles.map((pile) => describePile(pile, writtenOff)).join(", ") : void 0;
    },
    // The inverse of lumberjacking's makeBoards: here the ore is double-clicked and the beetle is the
    // target, the same as walking up to a forge
    perform: (stack) => {
      if (!forge) {
        return false;
      }
      if (target.open) {
        target.cancel();
      }
      journal.clear();
      player.use(stack.serial);
      if (!target.waitTargetEntity(forge.serial, TARGET_TIMEOUT)) {
        target.cancel();
        log("smelt: no target cursor for the beetle");
        return false;
      }
      return true;
    },
    known: () => [ORE_GRAPHICS, INGOT_GRAPHICS],
    learn: (graphic) => INGOT_GRAPHICS.add(graphic),
    learned: "ingot graphic"
  });
  var unsmeltable = converter.writtenOff;
  var retryUnsmeltable = converter.retry;
  var smeltAgainst = (reach) => {
    if (!nextOre(converter.writtenOff)) {
      return converter.run();
    }
    const found = findBeetle();
    if (!found) {
      if (!reportedMissing) {
        log("smelt: no fire beetle nearby, keeping the ore as it is");
        reportedMissing = true;
      }
      return false;
    }
    reportedMissing = false;
    forge = reach(found.serial);
    if (!forge) {
      return false;
    }
    return converter.run();
  };
  var smeltAll = () => smeltAgainst(walkToBeetle);

  // src/mining/relieve.ts
  var tooHeavy = () => overweight();
  var createSmeltForRoom = (options) => {
    const stop = () => ({
      stop: `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, and smelting freed nothing` + (options.hint ? ` - ${options.hint}` : "")
    });
    return () => {
      if (!tooHeavy()) {
        return void 0;
      }
      const before = oreTotal();
      groupOres();
      options.smelt();
      if (oreTotal() < before) {
        return { phase: "smelting" };
      }
      if (isSaving()) {
        waitOutSave();
        return { phase: "smelting" };
      }
      if (retryUnsmeltable()) {
        return { phase: "smelting" };
      }
      groupOres();
      options.smelt();
      if (oreTotal() < before) {
        return { phase: "smelting" };
      }
      if (isSaving()) {
        waitOutSave();
        return { phase: "smelting" };
      }
      return stop();
    };
  };

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

  // src/mining/memory.ts
  var KEY = "__mining_memory";
  var VERSION = 1;
  var store = /* @__PURE__ */ createStore({
    key: KEY,
    version: VERSION,
    seed: () => ({ blocked: /* @__PURE__ */ new Map(), notOre: /* @__PURE__ */ new Set() }),
    describe: (found) => found.blocked.size > 0 || found.notOre.size > 0 ? `memory: resuming with ${found.blocked.size} blocked tiles, ${found.notOre.size} arts` : void 0
  });
  var memory = store.read;
  var forget = store.forget;

  // src/mining/vein.ts
  var known = /* @__PURE__ */ new Map();
  var artKey = (graphic, isLand) => `${isLand ? "land" : "static"}:${graphic}`;
  var isOre = (graphic, isLand) => {
    if (NOT_ORE_GRAPHICS.has(graphic) || memory().notOre.has(artKey(graphic, isLand))) {
      return false;
    }
    if (isLand) {
      return ORE_TILE_GRAPHICS.has(graphic);
    }
    const remembered = known.get(graphic);
    if (remembered !== void 0) {
      return remembered;
    }
    const name = client.getStatic(graphic)?.name ?? "";
    const matches2 = ORE_STATIC_NAME.test(name);
    known.set(graphic, matches2);
    return matches2;
  };
  var store2 = /* @__PURE__ */ createTileStore({
    label: "vein",
    blocked: () => memory().blocked,
    depletedFor: RESPAWN_DELAY,
    unreachableFor: UNREACHABLE_DELAY,
    depleted: "is out of ore"
  });
  var markDepleted = store2.markDepleted;
  var markUnreachable = store2.markUnreachable;
  var markUnusable = store2.markUnusable;
  var markAreaDepleted = (range2) => {
    const until = now() + RESPAWN_DELAY;
    let parked = 0;
    for (let dx = -range2; dx <= range2; dx++) {
      for (let dy = -range2; dy <= range2; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          if (!isOre(tile.graphic, tile.isLand)) {
            continue;
          }
          store2.block(
            { x: tile.x, y: tile.y, z: tile.z, graphic: tile.graphic, isLand: tile.isLand },
            until
          );
          parked++;
        }
      }
    }
    log(
      `vein: nothing harvestable at ${player.x},${player.y}, parking ${parked} tile(s) within ${range2} for ${Math.max(1, Math.round(RESPAWN_DELAY / 6e4))}m`
    );
    return parked;
  };
  var markNotMineable = (tile) => {
    const { notOre } = memory();
    const key = artKey(tile.graphic, tile.isLand);
    if (notOre.has(key)) {
      return;
    }
    notOre.add(key);
    log(`vein: ${hex(tile.graphic)} cannot be mined, skipping that art from here on`);
  };
  var scan = /* @__PURE__ */ createScan({
    label: "scanForVein",
    radius: SCAN_RADIUS,
    blocked: () => memory().blocked,
    matches: isOre,
    // Land is not skipped the way lumberjacking skips it - a mountainside *is* land, and it is the
    // ordinary case rather than the exception
    describe: (vein) => `'${vein.isLand ? "land" : client.getStatic(vein.graphic)?.name ?? "?"}'`
  });
  var current;
  var stillOre = (vein) => {
    const until = store2.blockedUntil(vein);
    if (until !== void 0 && now() < until) {
      return void 0;
    }
    for (const tile of client.getTerrainList(vein.x, vein.y) ?? []) {
      if (tile.z === vein.z && tile.graphic === vein.graphic && tile.isLand === vein.isLand) {
        return isOre(tile.graphic, tile.isLand) ? { ...vein, distance: distanceTo(vein) } : void 0;
      }
    }
    return void 0;
  };
  var scanForVein = () => {
    if (current) {
      current = stillOre(current);
      if (current) {
        return { vein: current };
      }
    }
    const near = scan(MINE_RANGE);
    if (near.found) {
      current = near.found;
      return { vein: current };
    }
    const { found, readyAt } = scan();
    current = found;
    return { vein: found, respawnsAt: readyAt };
  };

  // src/mining/survey.ts
  var surveyTerrain = (radius) => {
    const seen = /* @__PURE__ */ new Map();
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          const key = `${tile.graphic}/${tile.isLand}`;
          const already = seen.get(key);
          if (already) {
            already.tiles++;
            continue;
          }
          seen.set(key, {
            graphic: tile.graphic,
            isLand: tile.isLand,
            flags: tile.flags,
            tiles: 1,
            name: tile.isLand ? "" : client.getStatic(tile.graphic)?.name ?? "?",
            matches: isOre(tile.graphic, tile.isLand)
          });
        }
      }
    }
    return [...seen.values()].sort((a, b) => b.tiles - a.tiles);
  };
  var describeArt = (art) => {
    const kind = art.isLand ? "land" : `static '${art.name}'`;
    const mark = art.matches ? "MATCHES" : "-";
    return `${art.graphic} (0x${art.graphic.toString(16)}) ${kind}, flags 0x${art.flags.toString(16)}, ${art.tiles} tiles, ${mark}`;
  };
  var reportTerrain = (radius, limit = Infinity) => {
    const found = surveyTerrain(radius);
    log(`survey: ${found.length} distinct arts within ${radius} tiles of ${player.x},${player.y}`);
    for (const art of found.slice(0, limit)) {
      log(`survey: ${describeArt(art)}`);
    }
    if (found.length > limit) {
      log(`survey: ${found.length - limit} rarer arts not shown`);
    }
    return found;
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
    const describe2 = (hostile, friend) => {
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
        const said2 = options.attackText.some((text) => journal.containsText(text));
        const hostile = hostileNear();
        if (!hostile && !hurt && !friendHurt && !said2) {
          if (episode) {
            episode = false;
            calls = 0;
            log(`${options.prefix}: clear`);
          }
          return;
        }
        if (!episode) {
          episode = true;
          log(`${options.prefix}: trouble - ${describe2(hostile, friend)}`);
        }
        if (hurt || friendHurt || said2 || hostile && matches(hostile, options.callOnSight)) {
          callGuards();
        }
      }
    };
  };

  // src/mining/threat.ts
  var watchForTrouble = (prefix) => WATCH_FOR_TROUBLE ? createThreatWatch({
    prefix,
    range: THREAT_RANGE,
    hostile: HOSTILE_NOTORIETY,
    callOnSight: CALL_ON_SIGHT_NOTORIETY,
    companion: findBeetle,
    companionName: "beetle",
    call: GUARD_CALL,
    calls: GUARD_CALLS,
    callDelay: GUARD_CALL_DELAY,
    replyWait: GUARD_REPLY_WAIT,
    noGuardsText: NO_GUARDS_TEXT,
    attackText: ATTACK_TEXT,
    guardedText: GUARD_ZONE_TEXT,
    unguardedText: UNGUARDED_TEXT
  }).check : void 0;

  // src/mining/index.ts
  rememberPickaxe(player.equippedItems.oneHanded);
  var watch = watchForTrouble("mining");
  var idleUntil = createIdleWait({
    prefix: "mining",
    waitingFor: "everything in reach is worked out",
    pollMs: IDLE_POLL,
    logEveryMs: IDLE_LOG_EVERY,
    stopReason,
    watch,
    onDone: resetBeat
  });
  var groupAndSmelt = () => {
    groupOres();
    smeltAll();
  };
  log(`mining: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);
  log(
    `mining: mounted ${player.equippedItems.mount ? "yes" : "no"}, hand ${describeItem(player.equippedItems.oneHanded)}, weight ${player.weight}/${player.weightMax}`
  );
  var afoot = dismount();
  if (PICK_BEETLE) {
    pickBeetle();
  }
  groupOres();
  if (afoot && tooHeavy()) {
    smeltAll();
  }
  var barren = 0;
  var oreBefore = 0;
  var smeltForRoom = createSmeltForRoom({ smelt: smeltAll });
  var handle = (outcome, vein) => {
    if (!vein) {
      return void 0;
    }
    switch (outcome) {
      // Worked out, not dead: markDepleted times it out and the scan picks it up again in
      // RESPAWN_DELAY.
      case "empty":
        markDepleted(vein);
        groupAndSmelt();
        return {};
      // The shard answering about where you stand rather than about a tile. Everything in reach goes
      // on the respawn cooldown together so the loop walks off; parking only the vein it happened to
      // pick left the character swinging at the spot the shard had just written off, which is how a
      // run ended before this had a bucket of its own.
      case "nothingNearby":
        markAreaDepleted(MINE_RANGE);
        if (++barren === NOTHING_NEARBY_HINT) {
          log(
            `mining: ${NOTHING_NEARBY_HINT} spots in a row had nothing to harvest - ORE_TILE_GRAPHICS is probably matching ground that carries no ore`
          );
          reportTerrain(MINE_RANGE, SURVEY_ARTS);
        }
        groupAndSmelt();
        return {};
      // A wrong band in ORE_TILE_GRAPHICS is a whole stretch of mountain, so ban the graphic rather
      // than walking to its copies one at a time
      case "notOre":
        markNotMineable(vein);
        markUnusable(vein, "cannot be mined");
        return {};
      // Already inside MINE_RANGE, so the shard disagrees about the range rather than the walk having
      // fallen short
      case "tooFar":
        markUnusable(vein, `is out of reach at ${vein.distance} tiles`);
        return {};
      // Line of sight: walking closer would not help and neither would waiting
      case "notSeen":
        markUnusable(vein, "is not in line of sight");
        return {};
      // The ore this swing produced was destroyed rather than dropped, so swinging again destroys
      // more. A full pack is a container at its item cap, so consolidating is the fix: forty piles of
      // one become one pile of forty. If weight is the real problem, the next cycle smelts.
      case "packFull":
        log("mining: pack is full, consolidating before the next swing");
        groupOres();
        return {};
      default:
        return void 0;
    }
  };
  runHarvest({
    prefix: "mining",
    landed: "dug",
    toolName: "pickaxe",
    stopReason,
    watch,
    equipTool: equipPickaxe,
    ready: () => dismount() ? void 0 : "could not get off the mount",
    relieve: smeltForRoom,
    isSaving,
    waitOutSave,
    approach: createApproach({
      // Renamed rather than shared: 'vein' and 'respawnsAt' are what this folder's tests read
      scan: () => {
        const { vein, respawnsAt } = scanForVein();
        return { found: vein, readyAt: respawnsAt };
      },
      range: MINE_RANGE,
      maxSteps: MAX_STEPS,
      step: stepToward,
      markUnreachable,
      idleUntil,
      isSaving,
      nothingFound: () => {
        log("mining: nothing matched, here is what is actually on the ground");
        reportTerrain(SCAN_RADIUS, SURVEY_ARTS);
        return "no ore in range";
      }
    }),
    harvest: () => {
      oreBefore = oreTotal();
      return digOnce(pickaxeSerial());
    },
    // Ore arrives as a new pile rather than joining the one already there. Grouping every swing keeps
    // the pack at one pile per hue, so the item cap is never approached by pile count alone - packFull
    // destroys the ore of the swing that hits it - and nothing sits below MIN_SMELT_AMOUNT when the
    // smelt comes.
    onLanded: () => {
      barren = 0;
      waitForOre(oreBefore);
      groupOres();
    },
    handle,
    progress: (mined) => `${mined} swings, ${oreTotal()} ore`,
    // Smelted only if the run is ending over the limit: what is in the pack is a few swings' worth,
    // and a run that ended on a stop reason has usually ended because something is wrong.
    finish: (mined) => {
      groupOres();
      if (tooHeavy()) {
        smeltAll();
      }
      log(`mining: ${mined} swings, ${oreTotal()} ore still in the pack`);
    },
    stall: createStallWatch({
      prefix: "mining",
      without: "cycles without a swing landing",
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
