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

  // src/lib/pick.ts
  var resolveName = (serial, oplTimeout) => {
    const fromTooltip = (client.queryItemOPL(serial, oplTimeout)?.name ?? "").trim();
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
  var describe = (info, oplTimeout) => {
    const serial = info.serial ?? 0;
    const found = client.findObject(serial);
    return {
      serial,
      name: resolveName(serial, oplTimeout),
      graphic: info.graphic ?? found?.graphic ?? 0,
      hue: info.hue ?? found?.hue ?? 0
    };
  };
  var pickOne = ({ prefix, prompt, oplTimeout }) => {
    log(`${prefix}: ${prompt}`);
    const info = clicked(prefix);
    return info && describe(info, oplTimeout);
  };
  var pickMany = ({
    prefix,
    prompt,
    maxPicks,
    oplTimeout,
    keyOf,
    label
  }) => {
    const picks2 = [];
    const seen = /* @__PURE__ */ new Set();
    const name2 = label ?? ((picked) => picked.name);
    log(`${prefix}: ${prompt}`);
    let asked = 0;
    for (; asked < maxPicks; asked++) {
      const info = clicked(prefix);
      if (!info) {
        break;
      }
      const picked = describe(info, oplTimeout);
      const key = keyOf(picked);
      if (key === void 0) {
        continue;
      }
      if (seen.has(key)) {
        log(`${prefix}: '${name2(picked)}' is already on the list`);
        continue;
      }
      seen.add(key);
      picks2.push(picked);
      log(`${prefix}:   ${picks2.length}. ${name2(picked)}`);
    }
    if (asked === maxPicks) {
      log(`${prefix}: ${maxPicks} clicks is as many as one run takes`);
      target.cancel();
    }
    return picks2;
  };

  // src/transfer/config.ts
  var OPEN_DELAY = 800;
  var MOVE_DELAY = 600;
  var MAX_PASSES = 12;
  var MAX_PICKS = 20;
  var OPL_TIMEOUT = 2e3;
  var LOG_EVERY_ITEM = true;

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
  var isContainer = (item) => (contentsOf(item)?.length ?? 0) > 0 || CONTAINER_GRAPHICS.has(item.graphic);

  // src/transfer/move.ts
  var artKey = (item) => `${hex(item.graphic)}/${item.hue ?? 0}`;
  var wantedFrom = (picks2) => {
    if (picks2.length === 0) {
      return { has: () => true, describe: () => "everything" };
    }
    const keys = new Set(picks2.map((picked) => artKey(picked)));
    return { has: (item) => keys.has(artKey(item)), describe: () => [...keys].join(", ") };
  };
  var resolveItem = (serial) => {
    const found = client.findObject(serial);
    return found && !isMobile(found) ? found : void 0;
  };
  var holdsThings = (item, opened) => opened.has(item.serial) || isContainer(item);
  var walk = (contents, destSerial, opened, into) => {
    for (const item of contents ?? []) {
      if (item.serial === destSerial) {
        continue;
      }
      if (holdsThings(item, opened)) {
        into.containers.push(item);
        walk(contentsOf(item), destSerial, opened, into);
        continue;
      }
      into.loose.push(item);
    }
  };
  var survey = (sourceSerial, destSerial, opened) => {
    const contents = contentsOf(resolveItem(sourceSerial));
    const found = { loose: [], containers: [], readable: contents !== void 0 };
    walk(contents, destSerial, opened, found);
    return found;
  };
  var movables = (sourceSerial, destSerial, wanted2, opened = /* @__PURE__ */ new Set()) => survey(sourceSerial, destSerial, opened).loose.filter((item) => wanted2.has(item));
  var openNested = (sourceSerial, destSerial, opened) => {
    let openedAny = false;
    for (const bag of survey(sourceSerial, destSerial, opened).containers) {
      if (opened.has(bag.serial)) {
        continue;
      }
      opened.add(bag.serial);
      player.use(bag.serial);
      sleep(OPEN_DELAY);
      openedAny = true;
    }
    return openedAny;
  };
  var transfer = (sourceSerial, destSerial, wanted2, onMove) => {
    player.use(sourceSerial);
    sleep(OPEN_DELAY);
    const sent = /* @__PURE__ */ new Map();
    const opened = /* @__PURE__ */ new Set();
    const result = (outcome2, left2) => ({
      outcome: outcome2,
      stacks: sent.size,
      items: [...sent.values()].reduce((total, amount) => total + amount, 0),
      left: left2
    });
    let previous = Infinity;
    for (let pass = 0; pass < MAX_PASSES; pass++) {
      if (!survey(sourceSerial, destSerial, opened).readable) {
        return result("unopened", 0);
      }
      if (openNested(sourceSerial, destSerial, opened)) {
        previous = Infinity;
        continue;
      }
      const todo = movables(sourceSerial, destSerial, wanted2, opened);
      if (todo.length === 0) {
        return result("emptied", 0);
      }
      if (todo.length >= previous) {
        return result("stalled", todo.length);
      }
      previous = todo.length;
      for (const item of todo) {
        player.moveItem(item.serial, destSerial);
        sent.set(item.serial, item.amount ?? 1);
        onMove?.(item);
        sleep(MOVE_DELAY);
      }
    }
    return result("stalled", movables(sourceSerial, destSerial, wanted2, opened).length);
  };

  // src/transfer/index.ts
  var name = (picked) => `${picked.name || artKey(picked)} (${hex(picked.serial)})`;
  var source = pickOne({ prefix: "transfer", prompt: "target the container to empty", oplTimeout: OPL_TIMEOUT }) ?? die("transfer: no container to empty");
  var destination = pickOne({ prefix: "transfer", prompt: "target the container to fill", oplTimeout: OPL_TIMEOUT }) ?? die("transfer: nowhere to put it");
  if (destination.serial === source.serial) {
    die("transfer: that is the same container twice");
  }
  var picks = pickMany({
    prefix: "transfer",
    prompt: "target one of each item to move, ESC to move all of it",
    maxPicks: MAX_PICKS,
    oplTimeout: OPL_TIMEOUT,
    keyOf: artKey,
    label: (picked) => `${picked.name || "unnamed"} ${artKey(picked)}`
  });
  var wanted = wantedFrom(picks);
  log(`transfer: ${name(source)} -> ${name(destination)}, moving ${wanted.describe()}`);
  player.use(destination.serial);
  sleep(OPEN_DELAY);
  var { outcome, stacks, items, left } = transfer(
    source.serial,
    destination.serial,
    wanted,
    (item) => {
      if (LOG_EVERY_ITEM) {
        log(`transfer:   ${artKey(item)} x${item.amount ?? 1}`);
      }
    }
  );
  var tally = `${stacks} stacks, ${items} items`;
  var reason = outcome === "emptied" ? `moved ${tally}` : outcome === "unopened" ? `${hex(source.serial)} would not open - stand closer, or open it yourself first` : `${left} left behind, nothing moved on the last pass - moved ${tally}`;
  exit(`transfer: ${reason}`);
})();
