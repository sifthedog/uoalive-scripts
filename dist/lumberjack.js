"use strict";
(() => {
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
  var isContainer = (item) => Array.isArray(item.contents) || CONTAINER_GRAPHICS.has(item.graphic);
  var openContainers = (preferredSerial) => {
    if (preferredSerial) {
      player.use(preferredSerial);
      sleep(800);
      return true;
    }
    let opened = false;
    for (const item of player.backpack?.contents ?? []) {
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
      if (item.contents && item.contents.length > 0) {
        const foundInSub = findIn(item.contents, matches);
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
      if (item.contents && item.contents.length > 0) {
        found.push(...collectIn(item.contents, matches));
      }
    }
    return found;
  };

  // src/lumberjacking/config.ts
  var AXE_NAME = "axe";
  var SPARE_BAG_SERIAL = void 0;
  var TREE_GRAPHICS = /* @__PURE__ */ new Set();
  var NOT_TREE_GRAPHICS = /* @__PURE__ */ new Set();
  var BOUNDS = { minX: 2400, maxX: 2580, minY: 400, maxY: 600 };
  var SCAN_RADIUS = 12;
  var CHOP_RANGE = 2;
  var LOG_GRAPHICS = /* @__PURE__ */ new Set([7133, 7136, 7134, 7135]);
  var BOARD_GRAPHICS = /* @__PURE__ */ new Set([7127, 7129, 7130, 7131]);
  var REGROW_DELAY = 25 * 60 * 1e3;
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var IDLE_POLL = 1e4;
  var IDLE_LOG_EVERY = 6e4;
  var STEP_DELAY = 300;
  var TARGET_TIMEOUT = 2e3;
  var CHOP_TIMEOUT = 8e3;
  var WALK_DELAY = 300;
  var PACK_ANIMAL_SERIALS = [];
  var PACK_ANIMAL_GRAPHICS = /* @__PURE__ */ new Set([291, 292, 791]);
  var UNLOAD_RANGE = 2;
  var HAUL_BUFFER = 120;
  var CONVERT_DELAY = 700;
  var MOVE_DELAY = 700;
  var CONVERT_TIMEOUT = 4e3;
  var CONVERT_POLL = 200;
  var CONVERT_ATTEMPTS = 3;
  var MAX_CONVERT_PASSES = 60;
  var UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill"
  ];
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
  var MAX_STEPS = 20;
  var WEIGHT_BUFFER = 40;
  var PACK_LIMIT = 120;
  var LOG_EVERY = 25;
  var SAVE_WAIT = 6e4;
  var SAVE_POLL = 1e3;
  var SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"];
  var SAVING_TEXT = ["The world is saving", "Saving world", "World save started"];
  var OUTCOME_TEXT = {
    chopped: ["You put", "You hack at the tree", "You chop some"],
    empty: ["There's not enough wood here to harvest", "There are no logs left"],
    // "You can't use an axe on that" is UOAlive's wording, seen on a live run against an
    // 'o'hii tree' static (0xc9e) - the tiledata calls it a tree, the shard will not harvest it
    notTree: [
      "You can't use an axe on that",
      "You can't chop that",
      "You can't use a bladed item on that",
      "You cannot chop"
    ],
    tooFar: ["That is too far away", "You cannot reach that"],
    // Confirmed from a live run. Line of sight, not range - the tile is inside CHOP_RANGE and the
    // shard still will not have it, so no amount of walking closer or waiting fixes it.
    notSeen: ["Target cannot be seen"],
    wornOut: ["You have worn out your tool"],
    // The shard freezing to write its world file. Nothing works while it does: the swing is refused,
    // the journal answers with none of the wordings above, and every cycle of it reads as an
    // unreadable outcome - five in a row and the run is over. It is not a failure of anything and
    // nothing about the tree is learned from it; it is a pause. Found on a live mining run.
    saving: SAVING_TEXT,
    // Full wordings first: the bare prefix also catches "You must wait N seconds" from systems that
    // have nothing to do with harvesting, and reading one of those as a chop throttle is how a swing
    // that was never refused ends up being retried forever. Kept last as a fallback all the same -
    // a phrase this list misses reads as an unreadable outcome, which is worse.
    throttled: ["You must wait to perform another action", "You must wait a moment", "You must wait"]
  };

  // src/lumberjacking/axe.ts
  var axeGraphic;
  var spareBagSerial = SPARE_BAG_SERIAL;
  var reportedEmpty = false;
  var held = () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded;
  var isAxe = (item) => axeGraphic !== void 0 && item.graphic === axeGraphic || (item.name ?? "").toLowerCase().includes(AXE_NAME);
  var rememberAxe = (item) => {
    if (item && axeGraphic === void 0) {
      axeGraphic = item.graphic;
      log(`axe graphic is 0x${item.graphic.toString(16)}`);
    }
  };
  var reportEmptyPack = () => {
    if (reportedEmpty) {
      return;
    }
    const graphics = (player.backpack?.contents ?? []).map((item) => `0x${item.graphic.toString(16)}`).join(", ");
    log(`equipAxe: no axe found. Top level of pack holds: ${graphics}`);
    reportedEmpty = true;
  };
  var stillHolding = () => {
    const item = held();
    if (!item || !isAxe(item)) {
      return false;
    }
    return client.findObject(item.serial) !== void 0;
  };
  var axeSerial = () => held()?.serial;
  var equipAxe = () => {
    if (stillHolding()) {
      return true;
    }
    let axe = findIn(player.backpack?.contents, isAxe);
    if (!axe && openContainers(spareBagSerial)) {
      axe = findIn(player.backpack?.contents, isAxe);
    }
    if (!axe) {
      client.headMsg("No axe!", player, 33);
      reportEmptyPack();
      return false;
    }
    reportedEmpty = false;
    rememberAxe(axe);
    if (axe.container && axe.container !== player.backpack?.serial) {
      spareBagSerial = axe.container;
    }
    target.cancel();
    for (let attempt = 1; attempt <= EQUIP_ATTEMPTS; attempt++) {
      player.equip(axe.serial);
      for (let waited = 0; waited < EQUIP_TIMEOUT; waited += EQUIP_POLL) {
        sleep(EQUIP_POLL);
        if (held()?.serial === axe.serial) {
          return true;
        }
      }
      log(`equipAxe: attempt ${attempt} did not land, reissuing`);
    }
    log("equipAxe: gave up equipping");
    return false;
  };

  // src/lib/pack.ts
  var countsByGraphic = (contents = player.backpack?.contents) => {
    const counts = /* @__PURE__ */ new Map();
    const walk = (items) => {
      for (const item of items ?? []) {
        const key = `0x${item.graphic.toString(16)}/${item.hue ?? 0}`;
        counts.set(key, (counts.get(key) ?? 0) + (item.amount ?? 1));
        walk(item.contents);
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

  // src/lumberjacking/chop.ts
  var ALL_OUTCOME_TEXT = Object.values(OUTCOME_TEXT).flat();
  var outcomeFor = (matched) => Object.keys(OUTCOME_TEXT).find((name) => OUTCOME_TEXT[name].includes(matched));
  var isLog = (item) => LOG_GRAPHICS.has(item.graphic);
  var totalIn = (contents) => (contents ?? []).reduce(
    (total, item) => total + (isLog(item) ? item.amount ?? 1 : 0) + totalIn(item.contents),
    0
  );
  var logTotal = (contents = player.backpack?.contents) => totalIn(contents);
  var silentOutcome = (serial, logsBefore) => {
    if (serial !== void 0 && !client.findObject(serial)) {
      return "wornOut";
    }
    if (logTotal() > logsBefore) {
      return "chopped";
    }
    return "unknown";
  };
  var chopOnce = (tree, serial) => {
    target.cancel();
    const logsBefore = logTotal();
    journal.clear();
    player.useItemInHand();
    if (!target.wait(TARGET_TIMEOUT)) {
      target.cancel();
      log("chopOnce: no target cursor, nothing usable in hand?");
      return "noCursor";
    }
    target.terrain(tree.x, tree.y, tree.z, tree.graphic);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CHOP_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(serial, logsBefore);
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
  var stopReason = () => {
    if (player.isDead) {
      return "you are dead";
    }
    if (!inBounds(player.x, player.y)) {
      return `at ${player.x},${player.y}, outside ${describeBounds()}`;
    }
    if (overweight(WEIGHT_BUFFER)) {
      return `overweight (${player.weight}/${player.weightMax})`;
    }
    const top = (player.backpack?.contents ?? []).length;
    if (top >= PACK_LIMIT) {
      return `pack is full (${top} items at the top level)`;
    }
    return void 0;
  };

  // src/lumberjacking/memory.ts
  var KEY = "__lumberjack_memory";
  var VERSION = 1;
  var now = () => Date.now();
  var scope = globalThis;
  var load = () => {
    const found = scope[KEY];
    if (found?.version === VERSION) {
      if (found.blocked.size > 0 || found.notTree.size > 0) {
        log(`memory: resuming with ${found.blocked.size} blocked tiles, ${found.notTree.size} arts`);
      }
      return found;
    }
    const store2 = { version: VERSION, blocked: /* @__PURE__ */ new Map(), notTree: /* @__PURE__ */ new Set() };
    scope[KEY] = store2;
    return store2;
  };
  var store;
  var memory = () => store ?? (store = load());

  // src/lumberjacking/heartbeat.ts
  var lastBeat;
  var beat = (phase, cycle, chopped2) => {
    const time = now();
    if (lastBeat === void 0) {
      lastBeat = time;
      return;
    }
    if (time - lastBeat < HEARTBEAT_EVERY) {
      return;
    }
    lastBeat = time;
    log(
      `lumberjack: still here - ${phase}, cycle ${cycle}, at ${player.x},${player.y}, ${player.weight}/${player.weightMax}, ${chopped2} chops`
    );
  };
  var resetBeat = () => {
    lastBeat = now();
  };

  // src/lumberjacking/save.ts
  var isSaving = () => SAVING_TEXT.some((text) => journal.containsText(text));
  var waitOutSave = () => {
    log("save: the world is saving, waiting it out");
    journal.clear();
    for (let waited = 0; waited < SAVE_WAIT; waited += SAVE_POLL) {
      sleep(SAVE_POLL);
      if (SAVE_DONE_TEXT.some((text) => journal.containsText(text))) {
        break;
      }
      if (stopReason()) {
        break;
      }
    }
    resetBeat();
  };

  // src/lumberjacking/boards.ts
  var unconvertible = /* @__PURE__ */ new Set();
  var isBoard = (item) => BOARD_GRAPHICS.has(item.graphic);
  var learnBoards = (changes) => {
    for (const { key, delta } of changes) {
      if (delta <= 0) {
        continue;
      }
      const graphic = Number(key.split("/")[0]);
      if (LOG_GRAPHICS.has(graphic) || BOARD_GRAPHICS.has(graphic)) {
        continue;
      }
      BOARD_GRAPHICS.add(graphic);
      log(`makeBoards: board graphic is 0x${graphic.toString(16)}`);
    }
  };
  var waitForChange = (before) => {
    for (let waited = 0; waited < CONVERT_TIMEOUT; waited += CONVERT_POLL) {
      sleep(CONVERT_POLL);
      const changes = diffCounts(before, countsByGraphic());
      if (changes.length > 0) {
        return changes;
      }
    }
    return [];
  };
  var misses = /* @__PURE__ */ new Map();
  var missed = (stackHue) => {
    const count = (misses.get(stackHue) ?? 0) + 1;
    misses.set(stackHue, count);
    if (count >= CONVERT_ATTEMPTS) {
      unconvertible.add(stackHue);
      log(`makeBoards: hue ${stackHue} failed ${count} times, leaving it as logs`);
    }
  };
  var convert = (stack) => {
    const stackHue = stack.hue ?? 0;
    const before = countsByGraphic();
    target.cancel();
    journal.clear();
    player.useItemInHand();
    if (!target.waitTargetEntity(stack.serial, TARGET_TIMEOUT)) {
      target.cancel();
      log("makeBoards: no target cursor, nothing usable in hand?");
      missed(stackHue);
      return false;
    }
    const changes = waitForChange(before);
    if (changes.length > 0) {
      misses.delete(stackHue);
      learnBoards(changes);
      return true;
    }
    if (UNSKILLED_TEXT.some((text) => journal.containsText(text))) {
      unconvertible.add(stackHue);
      log(`makeBoards: not skilled enough for hue ${stackHue}, leaving it as logs`);
      return false;
    }
    missed(stackHue);
    return false;
  };
  var makeBoards = () => {
    for (let pass = 0; pass < MAX_CONVERT_PASSES; pass++) {
      if (isSaving()) {
        log("makeBoards: the world is saving, leaving the logs for now");
        return false;
      }
      const stack = collectIn(player.backpack?.contents, isLog).find(
        (item) => !unconvertible.has(item.hue ?? 0)
      );
      if (!stack) {
        return true;
      }
      convert(stack);
      sleep(CONVERT_DELAY);
    }
    log(`makeBoards: hit the ${MAX_CONVERT_PASSES} pass backstop`);
    return false;
  };

  // src/lumberjacking/walk.ts
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
  var stepToward = (tree) => {
    const step = allowedStep(Math.sign(tree.x - player.x), Math.sign(tree.y - player.y));
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
    sleep(WALK_DELAY);
    player.run(direction);
    sleep(WALK_DELAY);
    return player.x !== beforeX || player.y !== beforeY;
  };

  // src/lumberjacking/haul.ts
  var isCargo = (item) => isBoard(item) || isLog(item) && unconvertible.has(item.hue ?? 0);
  var distanceTo = (entity) => Math.max(Math.abs(entity.x - player.x), Math.abs(entity.y - player.y));
  var isMobile = (entity) => entity._tag === "Mobile";
  var reported = false;
  var findPackAnimals = () => {
    if (PACK_ANIMAL_SERIALS.length > 0) {
      return PACK_ANIMAL_SERIALS.map((serial) => client.findObject(serial)).filter(
        (pinned) => pinned !== void 0 && isMobile(pinned)
      );
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
  var approach = (serial) => {
    for (let step = 0; step <= MAX_STEPS; step++) {
      const animal = client.findObject(serial);
      if (!animal) {
        log("haul: lost track of the pack animal");
        return false;
      }
      if (distanceTo(animal) <= UNLOAD_RANGE) {
        return true;
      }
      if (!stepToward(animal)) {
        log("haul: cannot reach the pack animal");
        return false;
      }
    }
    log(`haul: still not next to the pack animal after ${MAX_STEPS} steps`);
    return false;
  };
  var moveAll = (packSerial, matches) => {
    let previousStacks = Infinity;
    while (true) {
      const stacks = collectIn(player.backpack?.contents, matches);
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
  var nameOf = (animal) => animal.name ?? `0x${animal.serial.toString(16)}`;
  var unloadTo = (animals, matches) => {
    let moved = false;
    for (const animal of animals) {
      const before = collectIn(player.backpack?.contents, matches).length;
      if (before === 0) {
        break;
      }
      if (!approach(animal.serial)) {
        continue;
      }
      const pack = animalPack(animal);
      if (!pack) {
        log(`haul: '${nameOf(animal)}' has no reachable backpack`);
        continue;
      }
      moveAll(pack.serial, matches);
      const after = collectIn(player.backpack?.contents, matches).length;
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
    const moved = unloadTo(animals, isCargo);
    if (overweight(HAUL_BUFFER)) {
      const logs = collectIn(player.backpack?.contents, isLog);
      if (logs.length > 0) {
        const total = logs.reduce((sum, item) => sum + (item.amount ?? 1), 0);
        log(`haul: ${total} logs would not convert in time, moving them as logs`);
        return unloadTo(animals, isLog) || moved;
      }
    }
    return moved;
  };

  // src/lumberjacking/tree.ts
  var known = /* @__PURE__ */ new Map();
  var tileKey = (tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;
  var minutes = (ms) => Math.max(1, Math.round(ms / 6e4));
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
    const matches = /tree/i.test(name);
    known.set(graphic, matches);
    return matches;
  };
  var block = (tile, until) => memory().blocked.set(tileKey(tile), until);
  var markDepleted = (tile) => {
    block(tile, now() + REGROW_DELAY);
    log(`tree: ${tile.x},${tile.y} is out of wood, back in ${minutes(REGROW_DELAY)}m`);
  };
  var markUnreachable = (tile) => {
    block(tile, now() + UNREACHABLE_DELAY);
    log(`tree: ${tile.x},${tile.y} could not be walked to, retrying in ${minutes(UNREACHABLE_DELAY)}m`);
  };
  var markUnusable = (tile, reason) => {
    block(tile, Infinity);
    log(`tree: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
  };
  var markNotHarvestable = (graphic) => {
    const { notTree } = memory();
    if (notTree.has(graphic)) {
      return;
    }
    notTree.add(graphic);
    log(`tree: 0x${graphic.toString(16)} cannot be chopped, skipping that art from here on`);
  };
  var reportedGraphics = /* @__PURE__ */ new Set();
  var distanceTo2 = (x, y) => Math.max(Math.abs(x - player.x), Math.abs(y - player.y));
  var scanForTree = () => {
    const { blocked } = memory();
    const time = now();
    let best;
    let regrowsAt;
    for (let dx = -SCAN_RADIUS; dx <= SCAN_RADIUS; dx++) {
      for (let dy = -SCAN_RADIUS; dy <= SCAN_RADIUS; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          if (tile.isLand || !isTree(tile.graphic)) {
            continue;
          }
          const tree = {
            x: tile.x,
            y: tile.y,
            z: tile.z,
            graphic: tile.graphic,
            distance: distanceTo2(tile.x, tile.y)
          };
          if (!reachableFromBounds(tree.x, tree.y, CHOP_RANGE)) {
            continue;
          }
          const key = tileKey(tree);
          const until = blocked.get(key);
          if (until !== void 0) {
            if (time < until) {
              if (Number.isFinite(until) && (regrowsAt === void 0 || until < regrowsAt)) {
                regrowsAt = until;
              }
              continue;
            }
            blocked.delete(key);
          }
          if (!best || tree.distance < best.distance) {
            best = tree;
          }
        }
      }
    }
    if (best && !reportedGraphics.has(best.graphic)) {
      const name = client.getStatic(best.graphic)?.name ?? "?";
      log(`scanForTree: matching 0x${best.graphic.toString(16)} '${name}'`);
      reportedGraphics.add(best.graphic);
    }
    return { tree: best, regrowsAt };
  };

  // src/lumberjacking/index.ts
  rememberAxe(player.equippedItems.twoHanded ?? player.equippedItems.oneHanded);
  var minutesLeft = (until) => Math.max(1, Math.round((until - now()) / 6e4));
  var idleUntil = (regrowsAt) => {
    const wait = regrowsAt - now();
    if (wait <= 0) {
      return;
    }
    log(`lumberjack: everything in reach is regrowing, waiting ${minutesLeft(regrowsAt)}m`);
    const slices = Math.ceil(wait / IDLE_POLL);
    let since = 0;
    for (let slice = 0; slice < slices && now() < regrowsAt; slice++) {
      sleep(IDLE_POLL);
      since += IDLE_POLL;
      if (stopReason()) {
        return;
      }
      if (since >= IDLE_LOG_EVERY) {
        since = 0;
        log(`lumberjack: ${minutesLeft(regrowsAt)}m to go`);
      }
    }
    resetBeat();
  };
  log(`lumberjack: ${logTotal()} logs in the pack to start, staying within ${describeBounds()}`);
  var chopped = 0;
  var unknown = 0;
  var stop;
  var reported2 = 0;
  var throttled = 0;
  var sinceProgress = 0;
  var hauling = true;
  var walkingTo;
  var steps = 0;
  var endCycle = (phase, cycle) => {
    beat(phase, cycle, chopped);
    sinceProgress++;
    if (sinceProgress === STALL_WARN) {
      log(`lumberjack: ${STALL_WARN} cycles without a chop, last was '${phase}'`);
    }
    if (sinceProgress >= STALL_STOP) {
      stop = `no progress in ${STALL_STOP} cycles, last was '${phase}'`;
    }
  };
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (!equipAxe()) {
      stop = "no axe";
      break;
    }
    if (hauling && overweight(HAUL_BUFFER)) {
      const weightBefore = player.weight;
      makeBoards();
      unload();
      if (isSaving()) {
        waitOutSave();
      } else if (player.weight >= weightBefore) {
        hauling = false;
        log("lumberjack: hauling freed nothing, carrying on until overweight");
      }
      endCycle("hauling", cycle);
      sleep(STEP_DELAY);
      continue;
    }
    const { tree, regrowsAt } = scanForTree();
    if (!tree) {
      if (regrowsAt === void 0) {
        stop = "no tree in range";
        break;
      }
      idleUntil(regrowsAt);
      continue;
    }
    if (tree.distance > CHOP_RANGE) {
      const key = `${tree.x},${tree.y}`;
      if (key !== walkingTo) {
        walkingTo = key;
        steps = 0;
      }
      if (!stepToward(tree) || ++steps > MAX_STEPS) {
        markUnreachable(tree);
        walkingTo = void 0;
      }
      endCycle("walking", cycle);
      continue;
    }
    walkingTo = void 0;
    const outcome = chopOnce(tree, axeSerial());
    switch (outcome) {
      case "chopped":
        chopped++;
        unknown = 0;
        throttled = 0;
        sinceProgress = 0;
        break;
      // A stump, not a dead tile: markDepleted times it out and the scan picks it up again later
      case "empty":
        markDepleted(tree);
        unknown = 0;
        break;
      // The whole art is scenery, not just this tile, so ban the graphic and the rest of the
      // forest's copies of it stop being walked to one at a time
      case "notTree":
        markNotHarvestable(tree.graphic);
        markUnusable(tree, "is not harvestable");
        unknown = 0;
        break;
      // Already inside CHOP_RANGE, so this is the shard disagreeing about the range rather than a
      // walk that fell short. Treat the tile as unreachable instead of swinging at it again.
      case "tooFar":
        markUnusable(tree, `is out of reach at ${tree.distance} tiles`);
        unknown = 0;
        break;
      // Line of sight, so walking closer would not help and neither would waiting - something is
      // simply in the way. Without this the tile reads as an unreadable outcome, is picked again by
      // the very next scan, and five of them in a row end the run.
      case "notSeen":
        markUnusable(tree, "is not in line of sight");
        unknown = 0;
        break;
      case "wornOut":
        log("lumberjack: axe worn out, swapping");
        unknown = 0;
        break;
      // Nothing was learned about the tree and nothing went wrong: the shard was busy. The counters
      // are reset rather than merely left alone, because whatever they had accumulated was measured
      // against a server that was not answering.
      // Sitting out a save is the script working, not the script stuck, so the stall watchdog is
      // reset along with the rest: a shard that saves often would otherwise walk a run to STALL_STOP
      // a save at a time, and the regrow wait is already excused on exactly this reasoning.
      case "saving":
        waitOutSave();
        unknown = 0;
        throttled = 0;
        sinceProgress = 0;
        break;
      // The one branch that used to say nothing and count nothing. A fixed 600ms retry is shorter
      // than the harvest delay on most shards, so the swing that was refused re-armed the very timer
      // it was waiting on - silently, standing still, for as long as the cycle backstop allowed.
      // Back off further each time instead, and give up rather than spin.
      case "throttled":
        throttled++;
        unknown = 0;
        log(`lumberjack: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
        sleep(Math.min(THROTTLE_BACKOFF * throttled, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the swing";
        }
        break;
      // A cursor that never opened, with an axe demonstrably in hand, is the shard declining to start
      // the swing rather than an empty hand - on a live mining run that was a third of them. Backed
      // off like a throttle, but still counted: five in a row with nothing else happening is a stuck
      // run whatever the cause.
      case "noCursor":
        unknown++;
        sleep(THROTTLE_BACKOFF);
        break;
      default:
        unknown++;
        log(`lumberjack: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
    }
    if (unknown >= MAX_UNKNOWN) {
      stop = `${MAX_UNKNOWN} unreadable outcomes in a row`;
      break;
    }
    if (chopped >= reported2 + LOG_EVERY) {
      reported2 = chopped;
      log(`lumberjack: ${chopped} chops, ${logTotal()} logs, ${player.weight}/${player.weightMax}`);
    }
    endCycle(outcome ?? "unknown", cycle);
    sleep(STEP_DELAY);
  }
  makeBoards();
  if (hauling) {
    unload();
  }
  log(`lumberjack: ${chopped} chops, ${logTotal()} logs still in the pack`);
  exit(`lumberjack: ${stop ?? `hit the ${MAX_CYCLES} cycle backstop`}`);
})();
