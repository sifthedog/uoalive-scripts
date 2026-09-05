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

  // src/lib/arts.ts
  var CORPSE_GRAPHIC = 8198;

  // src/corpse/config.ts
  var OPEN_RANGE = 2;
  var SCAN_RANGE = 18;
  var MAX_OPL_ASKS = 8;
  var OPL_TIMEOUT = 2e3;
  var OPEN_DELAY = 800;
  var SETTLE_POLL = 100;
  var SETTLE_TIMEOUT = 2e3;
  var LOG_ITEMS = 40;
  var CORPSE_PREFIX = "a corpse of ";

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

  // src/corpse/corpses.ts
  var onGround = () => client.findAllItemsOfType(CORPSE_GRAPHIC, void 0, "world").filter((item) => item.graphic !== 0);
  var inRange = (corpses, range) => corpses.filter((corpse) => distanceTo(corpse) <= range);
  var nearest = (corpses) => corpses.reduce(
    (best, corpse) => Math.min(distanceTo(corpse), best ?? Infinity),
    void 0
  );
  var survey = (corpses, asks, oplTimeout) => {
    const sorted = [...corpses].sort((a, b) => distanceTo(a) - distanceTo(b));
    let spent = 0;
    return sorted.map((corpse) => {
      let name = (corpse.name ?? "").trim();
      if (!name && spent < asks) {
        spent++;
        name = (queryOPL(corpse.serial, oplTimeout, "corpse")?.name ?? "").trim();
      }
      return { serial: corpse.serial, name, distance: distanceTo(corpse) };
    });
  };
  var words = (text) => text.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
  var hasWord = (text, word) => words(text).includes(word);
  var matchOf = (name, playerName) => {
    const corpse = name.trim().toLowerCase();
    const me2 = playerName.trim().toLowerCase();
    if (!corpse || !me2) {
      return void 0;
    }
    if (corpse.startsWith(CORPSE_PREFIX) && corpse.slice(CORPSE_PREFIX.length).trim() === me2) {
      return "exact";
    }
    return hasWord(corpse, me2) ? "loose" : void 0;
  };
  var RANK = { exact: 0, loose: 1, nearest: 2 };
  var chooseMine = (candidates2, playerName) => {
    const ranked = candidates2.map((candidate) => ({
      candidate,
      why: matchOf(candidate.name, playerName) ?? "nearest"
    })).sort((a, b) => RANK[a.why] - RANK[b.why] || a.candidate.distance - b.candidate.distance);
    const best = ranked[0];
    if (!best) {
      return void 0;
    }
    return {
      picked: best.candidate,
      why: best.why,
      named: ranked.filter((one) => one.why !== "nearest").length
    };
  };
  var describeGround = (corpses) => `${hex(CORPSE_GRAPHIC)} x${corpses.length}`;

  // src/lib/containers.ts
  var unreadable = /* @__PURE__ */ new Set();
  var complained = /* @__PURE__ */ new Set();
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

  // src/lib/sift.ts
  var artKey = (item) => `${hex(item.graphic)}/${item.hue ?? 0}`;

  // src/corpse/open.ts
  var corpseAt = (serial) => {
    const found = client.findObject(serial);
    return found && !isMobile(found) ? found : void 0;
  };
  var open = (serial, delays) => {
    player.use(serial);
    sleep(delays.openDelay);
    forgetUnreadable(serial);
    let contents2 = contentsOf(corpseAt(serial));
    for (let waited = 0; waited < delays.settleTimeout && contents2 === void 0; waited += delays.settlePoll) {
      sleep(delays.settlePoll);
      forgetUnreadable(serial);
      contents2 = contentsOf(corpseAt(serial));
    }
    if (!corpseAt(serial)) {
      return { outcome: "gone", contents: [] };
    }
    if (contents2 === void 0) {
      return { outcome: "unreadable", contents: [] };
    }
    return { outcome: contents2.length ? "opened" : "empty", contents: contents2 };
  };
  var describeHeld = (contents2, limit) => {
    if (contents2.length === 0) {
      return "nothing";
    }
    const totals = /* @__PURE__ */ new Map();
    for (const item of contents2) {
      const key = (item.name ?? "").trim() || artKey(item);
      totals.set(key, (totals.get(key) ?? 0) + (item.amount ?? 1));
    }
    const listed = [...totals].slice(0, limit).map(([key, count]) => `${key} x${count}`);
    const left = totals.size - listed.length;
    return listed.join(", ") + (left > 0 ? `, and ${left} more` : "");
  };

  // src/corpse/index.ts
  var me = (player.name ?? "").trim();
  if (!me) {
    log("corpse: the client has not said your name yet, so this can only take the nearest");
  }
  var all = onGround();
  log(`corpse: looking for '${me || "anyone"}' within ${SCAN_RANGE} tiles - ${describeGround(all)}`);
  if (all.length === 0) {
    die(
      `corpse: no corpses anywhere the client can see - if yours is on screen, ${hex(CORPSE_GRAPHIC)} is not this shard's corpse art`
    );
  }
  var near = inRange(all, SCAN_RANGE);
  if (near.length === 0) {
    die(
      `corpse: ${all.length} in the world, nearest ${nearest(all)} tiles away - nothing within ${SCAN_RANGE}`
    );
  }
  var candidates = survey(near, MAX_OPL_ASKS, OPL_TIMEOUT);
  var choice = chooseMine(candidates, me) ?? die("corpse: nothing to open");
  var { picked, why, named } = choice;
  var label = picked.name || hex(picked.serial);
  if (why === "nearest") {
    const unnamed = candidates.filter((one) => !one.name).length;
    log(
      `corpse: nothing here is named for you` + (unnamed ? ` (${unnamed} of ${candidates.length} would not say what they are)` : "") + ` - taking the nearest, '${label}' (${hex(picked.serial)}), ${picked.distance} tiles away`
    );
  } else {
    log(
      `corpse: '${picked.name}' (${hex(picked.serial)}) is yours, ${picked.distance} tiles away - ${why} name match`
    );
    if (named > 1) {
      log(`corpse: ${named} corpses here are named for you, taking the nearest`);
    }
  }
  if (picked.distance > OPEN_RANGE) {
    const other = candidates.find(
      (one) => one.distance <= OPEN_RANGE && one.serial !== picked.serial
    );
    die(
      other ? `corpse: yours is ${picked.distance} tiles away, and '${other.name || hex(other.serial)}' in reach is not yours - walk to yours and run it again` : `corpse: ${hex(picked.serial)} is ${picked.distance} tiles away - walk within ${OPEN_RANGE} and run it again`
    );
  }
  var { outcome, contents } = open(picked.serial, {
    openDelay: OPEN_DELAY,
    settlePoll: SETTLE_POLL,
    settleTimeout: SETTLE_TIMEOUT
  });
  if (outcome === "gone") {
    die(`corpse: ${hex(picked.serial)} is no longer there - it decayed, or someone moved it`);
  }
  if (outcome === "unreadable") {
    die(
      `corpse: ${hex(picked.serial)} would not say what it holds - the window may be up anyway; stand on it and run it again`
    );
  }
  if (outcome === "empty") {
    die(`corpse: '${label}' is open and reports nothing in it`);
  }
  log(`corpse: '${label}' holds ${describeHeld(contents, LOG_ITEMS)}`);
  var items = contents.reduce((total, one) => total + (one.amount ?? 1), 0);
  exit(`corpse: opened ${hex(picked.serial)} - ${contents.length} stacks, ${items} items`);
})();
