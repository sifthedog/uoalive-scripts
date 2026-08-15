"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;

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

  // src/boxes/config.ts
  var BOX_GRAPHICS = /* @__PURE__ */ new Set([2474, 3709, 3710]);
  var BOX_NAME = "wooden box";
  var DROP_KEYS = true;
  var DROP_SPREAD = [
    { x: 0, y: 0, z: 0 },
    { x: 1, y: 0, z: 0 },
    { x: 0, y: 1, z: 0 },
    { x: 1, y: 1, z: 0 },
    { x: -1, y: 0, z: 0 },
    { x: 0, y: -1, z: 0 },
    { x: -1, y: -1, z: 0 },
    { x: 1, y: -1, z: 0 },
    { x: -1, y: 1, z: 0 }
  ];
  var DROP_METHOD = "groundOffset";
  var DROP_TIMEOUT = 3e3;
  var DROP_POLL = 200;
  var KEY_GRAPHICS = /* @__PURE__ */ new Set([4110, 4111, 4112, 4113, 4114, 4115]);
  var SELL = false;
  var CLOSE_BOXES = "perBox";
  var CLOSE_TIMEOUT = 200;
  var LOG_EVERY_BOX = true;
  var KEEP = 0;
  var PEEK_CONTENTS = true;
  var OPL_TIMEOUT = 1e3;
  var OPEN_DELAY = 800;
  var MOVE_DELAY = 600;
  var GUMP_TIMEOUT = 5e3;
  var SELL_DELAY = 1500;
  var SALE_TIMEOUT = 3e3;
  var SALE_POLL = 200;
  var MAX_EMPTY_PASSES = 5;
  var MAX_SELL_PASSES = 10;
  var MAX_ROUNDS = 20;
  var WEIGHT_BUFFER = 40;
  var PACK_LIMIT = 120;

  // src/boxes/drop.ts
  var spread = 0;
  var nextTile = () => DROP_SPREAD[spread++ % DROP_SPREAD.length] ?? { x: 0, y: 0, z: 0 };
  var GROUND = 4294967295;
  var ATTEMPTS = {
    // The documented call. The offset is from the character, which dist/key-probe.js proved.
    groundOffset: (item, tile) => player.moveItemOnGroundOffset(item.serial, tile.x, tile.y, tile.z),
    // The same call one tile east, in case an offset of 0/0/0 reads as "do not move"
    groundOffsetStep: (item) => player.moveItemOnGroundOffset(item.serial, 1, 0, 0),
    // A drop addressed the way the protocol does it: the ground's own container serial, and the
    // world coordinates to land on
    worldSerial: (item, tile) => player.moveItem(item.serial, GROUND, player.x + tile.x, player.y + tile.y, player.z + tile.z)
  };
  var ORDER = ["groundOffset", "groundOffsetStep", "worldSerial"];
  var proven = DROP_METHOD === "auto" ? void 0 : DROP_METHOD;
  var exhausted = false;
  var containerOf = (serial) => {
    const found = client.findObject(serial);
    return found && found._tag !== "Mobile" ? found.container : void 0;
  };
  var left = (serial, from) => {
    for (let waited = 0; waited < DROP_TIMEOUT; waited += DROP_POLL) {
      sleep(DROP_POLL);
      if (containerOf(serial) !== from) {
        return true;
      }
    }
    return false;
  };
  var dropToGround = (item, from) => {
    if (exhausted) {
      return false;
    }
    const tile = nextTile();
    if (proven) {
      ATTEMPTS[proven](item, tile);
      return left(item.serial, from);
    }
    for (const candidate of ORDER) {
      ATTEMPTS[candidate](item, tile);
      if (left(item.serial, from)) {
        proven = candidate;
        log(`boxes: dropping works via '${candidate}' - pin it as DROP_METHOD to skip the retries`);
        return true;
      }
    }
    exhausted = true;
    log(
      `boxes: none of ${ORDER.join(", ")} would put a key on the floor. Keys are going into the pack instead - set DROP_KEYS = false to stop trying, and say so if you want another way in.`
    );
    return false;
  };

  // src/boxes/boxes.ts
  var boxGraphic;
  var keyGraphic;
  var isBox = (item) => boxGraphic !== void 0 && item.graphic === boxGraphic || BOX_GRAPHICS.has(item.graphic) || (item.name ?? "").toLowerCase().includes(BOX_NAME);
  var KEY_WORD = /\bkey\b/i;
  var isKey = (item) => keyGraphic !== void 0 && item.graphic === keyGraphic || KEY_GRAPHICS.has(item.graphic) || KEY_WORD.test(item.name ?? "");
  var rememberKey = (item) => {
    if (keyGraphic === void 0 && !KEY_GRAPHICS.has(item.graphic)) {
      keyGraphic = item.graphic;
      log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to KEY_GRAPHICS`);
    }
  };
  var rememberBox = (item) => {
    if (!item || boxGraphic !== void 0 || BOX_GRAPHICS.has(item.graphic)) {
      return false;
    }
    boxGraphic = item.graphic;
    log(`boxes: '${item.name}' is graphic ${hex(item.graphic)} - add it to BOX_GRAPHICS`);
    return true;
  };
  var findBoxes = () => {
    let boxes = collectIn(player.backpack?.contents, isBox);
    if (boxes.length === 0 && openContainers()) {
      boxes = collectIn(player.backpack?.contents, isBox);
    }
    if (rememberBox(boxes[0])) {
      boxes = collectIn(player.backpack?.contents, isBox);
    }
    return boxes;
  };
  var closeBox = (serial) => {
    if (CLOSE_BOXES !== "perBox") {
      return;
    }
    if (Gump.exists(serial)) {
      Gump.findOrWait(serial, CLOSE_TIMEOUT)?.close();
    }
  };
  var closeEverything = () => {
    if (CLOSE_BOXES === "allGumps") {
      client.closeAllGumps();
    }
  };
  var dumpPack = () => {
    log("boxes: pack contents (graphic / hue / amount / name)");
    for (const item of player.backpack?.contents ?? []) {
      log(
        `boxes:   ${hex(item.graphic)} hue ${item.hue ?? 0} x${item.amount ?? 1} "${item.name ?? ""}"`
      );
    }
  };
  var resolveItem = (serial) => {
    const found = client.findObject(serial);
    return found && found._tag !== "Mobile" ? found : void 0;
  };
  var emptyBox = (boxSerial, packSerial) => {
    player.use(boxSerial);
    sleep(OPEN_DELAY);
    const moved = /* @__PURE__ */ new Map();
    const keys = /* @__PURE__ */ new Map();
    const dropped = /* @__PURE__ */ new Map();
    const result = (outcome) => ({
      outcome,
      moved: [...moved.values()],
      keys: [...keys.values()],
      dropped: [...dropped.values()]
    });
    let previous = Infinity;
    for (let pass = 0; pass < MAX_EMPTY_PASSES; pass++) {
      const contents = resolveItem(boxSerial)?.contents;
      if (contents === void 0) {
        return result("unopened");
      }
      if (contents.length === 0) {
        return result("emptied");
      }
      if (contents.length >= previous) {
        return result("stalled");
      }
      previous = contents.length;
      for (const item of contents) {
        const looksLikeKey = isKey(item);
        if (looksLikeKey) {
          rememberKey(item);
          keys.set(item.serial, item);
        }
        if (looksLikeKey && DROP_KEYS && dropToGround(item, boxSerial)) {
          dropped.set(item.serial, item);
        } else {
          player.moveItem(item.serial, packSerial);
        }
        moved.set(item.serial, item);
        sleep(MOVE_DELAY);
      }
    }
    return result("stalled");
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

  // src/boxes/guards.ts
  var whenKeepingKeys = (guard) => () => {
    if (DROP_KEYS) {
      return void 0;
    }
    const reason = guard();
    return reason && `${reason} and keys are going into the pack`;
  };
  var stopReason = () => firstReason(
    dead,
    whenKeepingKeys(heavy(WEIGHT_BUFFER)),
    whenKeepingKeys(packFull(PACK_LIMIT))
  );

  // src/boxes/peek.ts
  var oplReportsContents = true;
  var textOf = (property) => {
    const values = (property.values ?? []).map((value) => value.text).join(" ");
    return `${property.text ?? ""} ${values}`;
  };
  var peekContents = (serial) => {
    if (!PEEK_CONTENTS || !oplReportsContents) {
      return void 0;
    }
    const opl = client.queryItemOPL(serial, OPL_TIMEOUT);
    for (const property of opl?.properties ?? []) {
      const match = textOf(property).match(/contents[^0-9]*([0-9]+)/i);
      if (match) {
        return Number(match[1]);
      }
    }
    oplReportsContents = false;
    log('boxes: no "contents" line in the tooltips here, so every box has to be opened to be checked');
    return void 0;
  };

  // src/lib/vendor.ts
  var namedExactly = (name) => (entry) => (entry.name ?? "").toLowerCase() === name.toLowerCase();
  var withKeepBack = (matches, keep) => {
    let remaining = keep;
    const toSell = [];
    for (const item of matches) {
      const amount = item.amount ?? 1;
      if (remaining >= amount) {
        remaining -= amount;
        continue;
      }
      toSell.push({ serial: item.serial, amount: amount - remaining });
      remaining = 0;
    }
    return toSell;
  };
  var totalOf = (entries) => entries.reduce((sum, entry) => sum + (entry.amount ?? 1), 0);
  var packLeft = (serials) => {
    const left2 = /* @__PURE__ */ new Map();
    for (const item of collectIn(packContents(), (held) => serials.has(held.serial))) {
      left2.set(item.serial, (left2.get(item.serial) ?? 0) + (item.amount ?? 1));
    }
    return left2;
  };
  var waitForSaleBySerial = (offered, timeoutMs, pollMs) => {
    const serials = new Set(offered.map((item) => item.serial));
    let left2 = /* @__PURE__ */ new Map();
    let remaining = offered.reduce((sum, item) => sum + item.amount, 0);
    for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
      sleep(pollMs);
      left2 = packLeft(serials);
      remaining = [...left2.values()].reduce((sum, amount) => sum + amount, 0);
    }
    return new Map(
      offered.map((item) => [item.serial, Math.max(0, item.amount - (left2.get(item.serial) ?? 0))])
    );
  };
  var waitForSale = (offered, timeoutMs, pollMs) => [...waitForSaleBySerial(offered, timeoutMs, pollMs).values()].reduce(
    (sum, taken) => sum + taken,
    0
  );
  var openSellGump = (prefix, timeoutMs) => {
    player.say("vendor sell");
    const data = Gump.waitForVendorGumpData(timeoutMs);
    if (!data) {
      log(`${prefix}: no vendor gump appeared - out of earshot?`);
      return void 0;
    }
    if (data.type !== "sell") {
      log(`${prefix}: got a '${data.type}' gump instead of a sell gump`);
      return void 0;
    }
    return { vendor: data.vendor, items: data.items ?? [] };
  };

  // src/boxes/sale.ts
  var isBoxEntry = namedExactly(BOX_NAME);
  var pickOffer = (items, emptied2, skipped) => {
    const named = items.filter(isBoxEntry);
    if (named.length === 0) {
      return { kind: "none", listed: [...new Set(items.map((item) => item.name))] };
    }
    if (skipped === 0) {
      return { kind: "offer", entries: named };
    }
    const bySerial = named.filter((entry) => emptied2.has(entry.serial));
    return bySerial.length === 0 ? { kind: "mismatch", named: named.length } : { kind: "offer", entries: bySerial };
  };
  var stillSellable = (emptied2, skipped) => (player.backpack?.contents ?? []).filter(
    (item) => isBox(item) && (skipped === 0 || emptied2.has(item.serial))
  ).length;
  var sellBoxes = (emptied2, skipped) => {
    let sold = 0;
    for (let pass = 0; pass < MAX_SELL_PASSES; pass++) {
      const data = openSellGump("boxes", GUMP_TIMEOUT);
      if (!data) {
        break;
      }
      const offer = pickOffer(data.items, emptied2, skipped);
      if (offer.kind === "none") {
        log(`boxes: no '${BOX_NAME}' on offer. Vendor listed: ${offer.listed.join(", ")}`);
        break;
      }
      if (offer.kind === "mismatch") {
        log(
          `boxes: the vendor lists ${offer.named} x ${BOX_NAME} but none of their serials match the boxes this run emptied, so selling by name could hand over a box that never opened. Stopping - empty the skipped boxes by hand and run again.`
        );
        break;
      }
      const toSell = withKeepBack(offer.entries, KEEP);
      if (toSell.length === 0) {
        log(`boxes: ${totalOf(offer.entries)} left, keeping them back`);
        break;
      }
      const offered = toSell.reduce((sum, entry) => sum + entry.amount, 0);
      client.sendSellRequest(data.vendor, toSell);
      const taken = waitForSale(toSell, SALE_TIMEOUT, SALE_POLL);
      sold += taken;
      log(`boxes: sell pass ${pass + 1}, offered ${offered} x ${BOX_NAME}, vendor took ${taken}`);
      if (taken === 0) {
        log(`boxes: stalled with ${offered} left, vendor is not taking them`);
        break;
      }
      if (stillSellable(emptied2, skipped) <= KEEP) {
        break;
      }
      sleep(SELL_DELAY);
    }
    return sold;
  };

  // src/boxes/index.ts
  var backpack = player.backpack ?? die("boxes: no backpack");
  var emptied = /* @__PURE__ */ new Set();
  var refused = /* @__PURE__ */ new Set();
  var stop;
  var keysSeen = 0;
  var keysDropped = 0;
  var keptBack = 0;
  var soldTotal = 0;
  var graphicsSeen = /* @__PURE__ */ new Set();
  var initial = findBoxes();
  log(`boxes: ${initial.length} wooden boxes in the pack`);
  if (initial.length === 0) {
    dumpPack();
    die("boxes: nothing matched - pick your box out of the dump above and put its graphic in BOX_GRAPHICS");
  }
  for (let round = 0; round < MAX_ROUNDS && !stop; round++) {
    const todo = findBoxes().filter((box) => !emptied.has(box.serial) && !refused.has(box.serial));
    let guard;
    let openedThisRound = 0;
    let skippedEmpty = 0;
    for (const box of todo) {
      guard = stopReason();
      if (guard) {
        break;
      }
      const inside = peekContents(box.serial);
      if (inside === 0) {
        emptied.add(box.serial);
        skippedEmpty++;
        if (LOG_EVERY_BOX) {
          log(`boxes: ${hex(box.serial)} already empty, not opening it`);
        }
        continue;
      }
      const { outcome, moved, keys, dropped } = emptyBox(box.serial, backpack.serial);
      keysSeen += keys.length;
      keysDropped += dropped.length;
      keptBack += moved.length - dropped.length;
      for (const item of moved) {
        graphicsSeen.add(item.graphic);
      }
      if (outcome === "emptied") {
        emptied.add(box.serial);
        openedThisRound++;
      } else {
        refused.add(box.serial);
      }
      closeBox(box.serial);
      if (LOG_EVERY_BOX) {
        const describe = (item) => `${hex(item.graphic)}${dropped.includes(item) ? " -> floor" : " -> pack"}`;
        const contents = moved.map(describe).join(", ") || "nothing";
        log(`boxes: ${hex(box.serial)} ${outcome}, took out ${contents}`);
      }
    }
    const skippedNote = skippedEmpty ? `, ${skippedEmpty} already empty` : "";
    const refusedNote = refused.size ? `, ${refused.size} would not open` : "";
    log(`boxes: round ${round + 1}, emptied ${openedThisRound}${skippedNote}${refusedNote}`);
    if (guard) {
      log(`boxes: stopped going through the boxes - ${guard}`);
    }
    if (!SELL) {
      stop = guard ?? `SELL is off, ${emptied.size} boxes emptied and left in the pack`;
      break;
    }
    const unconfirmed = findBoxes().filter((box) => !emptied.has(box.serial)).length;
    const sold = sellBoxes(emptied, unconfirmed);
    soldTotal += sold;
    if (sold === 0) {
      stop = openedThisRound + skippedEmpty ? "the vendor took nothing" : guard ?? "nothing left to empty and nothing sold";
      break;
    }
    if (todo.length === 0) {
      stop = refused.size ? `${refused.size} boxes would not open, everything else is dealt with` : "every box is dealt with";
    }
  }
  closeEverything();
  var keptNote = keptBack ? `, ${keptBack} other items into the pack` : "";
  log(
    `boxes: ${soldTotal} sold, ${keysDropped} of ${keysSeen} keys on the floor${keptNote}, ${refused.size} boxes left unopened. Graphics taken out of boxes: ${[...graphicsSeen].map(hex).join(", ") || "none"}`
  );
  if (keysSeen === 0 && keptBack > 0) {
    log(
      "boxes: nothing came out of a box looked like a key, so it all went into the pack. Put the graphic listed above into KEY_GRAPHICS in config.ts."
    );
  } else if (DROP_KEYS && keysDropped < keysSeen) {
    log(`boxes: ${keysSeen - keysDropped} keys were recognised but would not leave the box.`);
  }
  exit(`boxes: ${stop ?? `hit the ${MAX_ROUNDS} round backstop`}`);
})();
