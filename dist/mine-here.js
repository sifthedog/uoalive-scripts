"use strict";
(() => {
  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var distanceTo = (spot) => Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));
  var isMobile = (entity) => entity._tag === "Mobile";
  var nameOf = (entity) => entity.name ?? hex(entity.serial);
  var describeItem = (item) => item ? `${hex(item.graphic)} '${item.name ?? ""}'` : "empty";

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

  // src/lib/weight.ts
  var overweight = (buffer = 0) => player.weightMax > 0 && player.weight > player.weightMax - buffer;

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var STEP_DELAY = 300;
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
  var RESPAWN_DELAY = 25 * 60 * 1e3;
  var DIG_TIMEOUT = 8e3;
  var ORE_GRAPHICS = /* @__PURE__ */ new Set([6583, 6586, 6585, 6584]);
  var ORE_NAME = /\bore\b/i;
  var COMBINE_DELAY = 700;
  var ORE_SETTLE_TIMEOUT = 1500;
  var ORE_SETTLE_POLL = 150;
  var FIRE_BEETLE_GRAPHICS = /* @__PURE__ */ new Set([169]);
  var FIRE_BEETLE_SERIAL = void 0;
  var BEETLE_SCAN_RADIUS = 18;
  var SMELT_RANGE = 2;
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
  var OUTCOME_TEXT = {
    dug: ["You dig some", "You put", "You loosen some rocks"],
    // What parks a vein for RESPAWN_DELAY. Both wordings are in the wild: RunUO says metal, some
    // shards say ore, and reading either one as unknown would stop the run on a worked-out vein.
    empty: [
      "There is no metal here to mine",
      "There is no ore here to mine",
      "You cannot mine there"
    ],
    // Confirmed from a live run on this shard. Distinct from `empty` because of that last word: this
    // one is the shard answering about everything within reach of where you are standing, which is
    // the only kind of answer a swing that names no tile can really get. It parks the whole area
    // rather than a tile, and that is what makes the character walk away - reading it as `empty`
    // would park one tile, swing again from the same spot, and get the same sentence back.
    nothingNearby: [
      "There are no harvestable resources nearby",
      "There is nothing here to harvest"
    ],
    // About the art rather than the tile, so the whole graphic is banned - the same lesson
    // lumberjacking learned when the tiledata called a whole family of statics a tree
    notOre: ["You can't mine that", "Try mining in rock", "You can only mine"],
    tooFar: ["That is too far away", "You cannot reach that"],
    // Line of sight, not range - the tile is inside MINE_RANGE and the shard still will not have it,
    // so no amount of walking closer or waiting fixes it
    notSeen: ["Target cannot be seen"],
    // The ore is destroyed when this fires, not dropped, so it has to trigger a smelt rather than
    // another swing. Lumberjacking has no equivalent: it stops on weight long before the item cap.
    packFull: ["Your backpack is full", "That container cannot hold more"],
    wornOut: ["You have worn out your tool"],
    // The shard freezing to write its world file. Nothing works while it does: the swing is refused,
    // the journal answers with none of the wordings above, and every cycle of it reads as an
    // unreadable outcome - five in a row and the run is over, which is what a save did to a live one.
    // It is not a failure of anything and nothing about the vein is learned from it; it is a pause.
    saving: SAVING_TEXT,
    // Shared with the smelt, which reads the same refusal with no outcomes to read it as: to the
    // conversion a throttle is silence, and silence is what writes a hue off. One list, so a wording
    // corrected against this shard's journal fixes both.
    throttled: THROTTLED_TEXT
  };

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat(),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name].includes(matched))
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
  var totalMatching = (matches, contents = packContents()) => (contents ?? []).reduce(
    (total, item) => total + (matches(item) ? item.amount ?? 1 : 0) + totalMatching(matches, contentsOf(item) ?? []),
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
  var oresByHue = () => {
    const groups = /* @__PURE__ */ new Map();
    for (const item of packContents() ?? []) {
      if (!isOrePile(item)) {
        continue;
      }
      const oreHue = item.hue ?? 0;
      const group = groups.get(oreHue);
      if (group) {
        group.push(item);
      } else {
        groups.set(oreHue, [item]);
      }
    }
    return groups;
  };
  var groupOres = () => {
    let previousPiles = Infinity;
    while (true) {
      const groups = oresByHue();
      const piles = [...groups.values()].reduce((total, items) => total + items.length, 0);
      if (piles >= previousPiles) {
        log(`groupOres: stalled at ${piles} piles`);
        return;
      }
      previousPiles = piles;
      let combined = false;
      for (const [oreHue, items] of groups) {
        if (items.length <= 1) {
          continue;
        }
        const primary = items.reduce((a, b) => (b.amount ?? 1) > (a.amount ?? 1) ? b : a);
        const dup = items.find((item) => item.serial !== primary.serial);
        if (!dup) {
          continue;
        }
        player.use(dup.serial);
        if (!target.waitTargetEntity(primary.serial, TARGET_TIMEOUT)) {
          log(`groupOres: no target cursor for hue ${oreHue}`);
          target.cancel();
        }
        combined = true;
        sleep(COMBINE_DELAY);
      }
      if (!combined) {
        return;
      }
    }
  };

  // src/mining/dig.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var silentOutcome = (serial, oreBefore) => {
    if (serial !== void 0 && !client.findObject(serial)) {
      return "wornOut";
    }
    if (oreTotal() > oreBefore) {
      return "dug";
    }
    return "unknown";
  };
  var refusedOutcome = (serial, oreBefore, cursorCameLate) => {
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, NO_CURSOR_READ);
    if (matched) {
      return outcomeFor(matched);
    }
    const silent = silentOutcome(serial, oreBefore);
    if (silent !== "unknown") {
      return silent;
    }
    log(
      `digOnce: no target cursor - hand ${describeItem(player.equippedItems.oneHanded)}, cursor ${cursorCameLate ? "came late" : "never opened"}`
    );
    return "noCursor";
  };
  var digOnce = (serial) => {
    target.cancel();
    const oreBefore = oreTotal();
    journal.clear();
    player.useItemInHand();
    if (!target.waitTargetSelf(TARGET_TIMEOUT)) {
      const cursorCameLate = target.open;
      target.cancel();
      return refusedOutcome(serial, oreBefore, cursorCameLate);
    }
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, DIG_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(serial, oreBefore);
  };

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var packFull = (limit) => () => {
    const top = (packContents() ?? []).length;
    return top >= limit ? `pack is full (${top} items at the top level)` : void 0;
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
    const convertOne = (stack) => {
      const hue = stack.hue ?? 0;
      const before = countsByGraphic();
      if (!options.perform(stack)) {
        missed(hue);
        return;
      }
      const changes = waitForChange(before);
      if (changes.length > 0) {
        misses.delete(hue);
        learnOutput(changes);
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
        if (writtenOff.size === 0) {
          return false;
        }
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

  // src/mining/smelt.ts
  var beetleSerial = FIRE_BEETLE_SERIAL;
  var reportedFound = false;
  var reportedMissing = false;
  var findBeetle = () => {
    if (beetleSerial !== void 0) {
      const pinned = client.findObject(beetleSerial);
      if (pinned && isMobile(pinned)) {
        return pinned;
      }
      if (FIRE_BEETLE_SERIAL !== void 0) {
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
  var beetleInRange = (serial) => {
    const found = client.findObject(serial);
    if (!found || !isMobile(found)) {
      log(`smelt: lost track of ${hex(serial)}`);
      return void 0;
    }
    const away = distanceTo(found);
    if (away > SMELT_RANGE) {
      log(`smelt: the beetle is ${away} tiles off and this run does not walk`);
      return void 0;
    }
    return found;
  };
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
    // The inverse of lumberjacking's makeBoards, which uses the tool and targets the resource: here
    // the ore is double-clicked and the beetle is the target, the same as walking up to a forge
    perform: (stack) => {
      if (!forge) {
        return false;
      }
      target.cancel();
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
  var smeltHere = () => smeltAgainst(beetleInRange);

  // src/mining/here.ts
  rememberPickaxe(player.equippedItems.oneHanded);
  var tooHeavy = () => overweight();
  var WORKED_OUT = "the spot is worked out";
  log(`mine-here: ${oreTotal()} ore in the pack to start, at ${player.x},${player.y}`);
  log(
    `mine-here: mounted ${player.equippedItems.mount ? "yes" : "no"}, hand ${describeItem(player.equippedItems.oneHanded)}, weight ${player.weight}/${player.weightMax}`
  );
  var mined = 0;
  var unknown = 0;
  var stop;
  var reported2 = 0;
  var throttled = 0;
  var noCursor = 0;
  var stall = createStallWatch({
    prefix: "mine-here",
    without: "cycles without a swing landing",
    warnAt: STALL_WARN,
    stopAt: STALL_STOP,
    heartbeat
  });
  var endCycle = (phase, cycle) => {
    stall.endCycle(phase, cycle, mined);
    stop ?? (stop = stall.reason());
  };
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (!dismount()) {
      stop = "could not get off the mount";
      break;
    }
    if (!equipPickaxe()) {
      stop = "no pickaxe";
      break;
    }
    if (tooHeavy()) {
      const oreBefore2 = oreTotal();
      groupOres();
      smeltHere();
      if (oreTotal() < oreBefore2) {
        endCycle("smelting", cycle);
        sleep(STEP_DELAY);
        continue;
      }
      if (retryUnsmeltable()) {
        endCycle("smelting", cycle);
        sleep(STEP_DELAY);
        continue;
      }
      stop = `overweight (${player.weight}/${player.weightMax}) with ${oreTotal()} ore left, and smelting freed nothing - the beetle has to be standing next to you`;
      break;
    }
    const oreBefore = oreTotal();
    const outcome = digOnce(pickaxeSerial());
    switch (outcome) {
      case "dug":
        mined++;
        unknown = 0;
        throttled = 0;
        stall.progressed();
        waitForOre(oreBefore);
        groupOres();
        break;
      // The two ways the shard says there is nothing left, and this script does not distinguish them.
      // In dist/mining.js they differ by scope - one parks a tile, the other parks everything within
      // reach - and the scope is what decides where to walk next. There is no next here and no tile
      // being booked, so both mean the same thing: the spot is worked out and the run is over.
      //
      // Smelted first, and this is the moment the whole run has been carrying ore towards: the swings
      // are finished, the character is standing exactly where it started, and the beetle that has been
      // following it is either in range now or was never going to be.
      case "empty":
      case "nothingNearby":
        groupOres();
        smeltHere();
        stop = WORKED_OUT;
        break;
      // "You can't mine that" about a swing that named no tile is the shard saying this spot is not
      // mineable at all. dist/mining.js bans the art and walks to a different one; there is nothing to
      // ban here and nowhere to walk, so it is an ending.
      case "notOre":
        stop = "nothing here can be mined";
        break;
      // Range and line of sight, for a swing aimed at where the character is standing. Neither can be
      // answered by moving, because moving is the one thing this script does not do - so they are
      // ended rather than retried, and named separately because they mean different things about the
      // spot: one is a shard that wanted a tile after all, the other is something in the way.
      case "tooFar":
        stop = "the shard says the ore is out of reach from where you are standing";
        break;
      case "notSeen":
        stop = "the shard cannot see the ore from where you are standing";
        break;
      // The ore this swing produced was destroyed rather than dropped, so swinging again would only
      // destroy more. Consolidating is the answer rather than smelting, because a full pack is a
      // container at its item cap: forty piles of one become one pile of forty, and thirty-nine slots
      // come back. If weight is the real problem, the next cycle's tooHeavy() branch smelts.
      case "packFull":
        log("mine-here: pack is full, consolidating before the next swing");
        groupOres();
        unknown = 0;
        break;
      case "wornOut":
        log("mine-here: pickaxe worn out, swapping");
        unknown = 0;
        break;
      // Nothing was learned and nothing went wrong: the shard was busy writing its world file. The
      // counters are reset rather than merely left alone, because whatever they had accumulated was
      // measured against a server that was not answering - and the stall watchdog with them, since a
      // shard that saves often would otherwise walk a run to STALL_STOP a save at a time.
      case "saving":
        waitOutSave();
        unknown = 0;
        throttled = 0;
        stall.progressed();
        break;
      // A fixed retry shorter than the harvest delay re-arms the very timer it is waiting on, so back
      // off further each time instead, and give up rather than spin
      case "throttled":
        throttled++;
        unknown = 0;
        log(`mine-here: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the swing";
        }
        break;
      // A cursor that never opened, with a pickaxe demonstrably in hand, is the shard declining to
      // start the swing rather than an empty hand. digOnce has already read the journal and the pack
      // looking for a reason, so what is left here is a refusal with nothing said about it: treated
      // like one, with the same growing backoff and a budget of its own.
      case "noCursor":
        noCursor++;
        log(`mine-here: no target cursor (${noCursor}/${MAX_NO_CURSOR}), backing off`);
        sleep(backoffFor(noCursor, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (noCursor >= MAX_NO_CURSOR) {
          stop = "the shard never opened a target cursor";
        }
        break;
      default:
        unknown++;
        log(`mine-here: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
    }
    if (outcome !== "noCursor") {
      noCursor = 0;
    }
    if (unknown >= MAX_UNKNOWN) {
      stop = `${MAX_UNKNOWN} unreadable outcomes in a row`;
      break;
    }
    if (mined >= reported2 + LOG_EVERY) {
      reported2 = mined;
      log(`mine-here: ${mined} swings, ${oreTotal()} ore, ${player.weight}/${player.weightMax}`);
    }
    endCycle(outcome ?? "unknown", cycle);
    sleep(STEP_DELAY);
  }
  groupOres();
  if (tooHeavy()) {
    smeltHere();
  }
  if (stop === WORKED_OUT && mined === 0) {
    log("mine-here: no swing ever landed - the character is probably not standing next to a vein");
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(`mine-here: ${mined} swings, ${oreTotal()} ore still in the pack`);
  log(`mine-here: stopping - ${reason}`);
  exit(`mine-here: ${reason}`);
})();
