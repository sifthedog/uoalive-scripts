"use strict";
(() => {
  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var isMobile = (entity) => entity._tag === "Mobile";

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

  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);

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
  var pickOne = ({ prefix, prompt, oplTimeout }) => {
    log(`${prefix}: ${prompt}`);
    const info = clicked(prefix);
    return info && describe2(info, oplTimeout, prefix);
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
      const picked = describe2(info, oplTimeout, prefix);
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

  // src/lib/sift.ts
  var artKey = (item) => `${hex(item.graphic)}/${item.hue ?? 0}`;
  var wantedFrom = (picks2) => {
    if (picks2.length === 0) {
      return { has: () => true, describe: () => "everything" };
    }
    const keys = new Set(picks2.map((picked) => artKey(picked)));
    return { has: (item) => keys.has(artKey(item)), describe: () => [...keys].join(", ") };
  };
  var holdsThings = (item, opened) => opened.has(item.serial) || isContainer(item);
  var walk = (contents, options, into) => {
    for (const item of contents ?? []) {
      if (item.serial === options.skipSerial) {
        continue;
      }
      if (options.isLoose?.(item)) {
        into.loose.push(item);
        continue;
      }
      if (holdsThings(item, options.opened)) {
        into.containers.push(item);
        walk(contentsOf(item), options, into);
        continue;
      }
      into.loose.push(item);
    }
  };
  var siftContents = (contents, options) => {
    const found = { loose: [], containers: [], readable: contents !== void 0 };
    walk(contents, options, found);
    return found;
  };
  var movables = (found, wanted2) => found.loose.filter((item) => wanted2.has(item));
  var openNested = (bags, opened, openDelay) => {
    let openedAny = false;
    for (const bag of bags) {
      if (opened.has(bag.serial)) {
        continue;
      }
      opened.add(bag.serial);
      player.use(bag.serial);
      sleep(openDelay);
      forgetUnreadable(bag.serial);
      openedAny = true;
    }
    return openedAny;
  };

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var HEARTBEAT_EVERY = 3e4;
  var SAVE_WAIT = 6e4;
  var SAVE_POLL = 1e3;
  var SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"];
  var SAVING_TEXT = ["The world is saving", "Saving world", "World save started"];
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

  // src/stow/config.ts
  var MAX_CYCLES = 2e4;
  var WATCH_POLL = 2e3;
  var OPEN_DELAY = 800;
  var MOVE_DELAY = 250;
  var SETTLE_TIMEOUT = 2e3;
  var SETTLE_POLL = 100;
  var OPEN_NESTED = true;
  var MAX_REOPENS = 3;
  var MAX_QUIET_STOWS = 5;
  var STOW_BACKOFF = 2e3;
  var STOW_BACKOFF_MAX = 6e4;
  var MAX_LOST_DEST = 30;
  var MAX_PICKS = 20;
  var OPL_TIMEOUT = 2e3;
  var LOG_EVERY_ITEM = false;

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

  // src/stow/guards.ts
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

  // src/stow/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "stow",
    noun: "stowed",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/stow/move.ts
  var issue = (items2, destSerial) => items2.map((item, index) => {
    if (index > 0) {
      sleep(MOVE_DELAY);
    }
    player.moveItem(item.serial, destSerial);
    return { serial: item.serial, amount: item.amount ?? 1 };
  });
  var landed = (sent, after) => {
    const left = new Set(after.map((item) => item.serial));
    const gone = sent.filter((moved) => !left.has(moved.serial));
    return {
      stacks: gone.length,
      items: gone.reduce((total, moved) => total + moved.amount, 0)
    };
  };
  var settle = (sent, rescan) => {
    let took = landed(sent, rescan());
    let waited = 0;
    for (; waited < SETTLE_TIMEOUT && took.stacks < sent.length; waited += SETTLE_POLL) {
      sleep(SETTLE_POLL);
      took = landed(sent, rescan());
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

  // src/stow/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    onDone: resetBeat
  });

  // src/stow/scan.ts
  var createScan = (options) => {
    const opened = /* @__PURE__ */ new Set();
    const reopens = /* @__PURE__ */ new Map();
    const rearm = (bags) => {
      for (const bag of bags) {
        if (!opened.has(bag.serial) || contentsOf(bag) !== void 0) {
          continue;
        }
        const spent = reopens.get(bag.serial) ?? 0;
        if (spent >= MAX_REOPENS) {
          continue;
        }
        reopens.set(bag.serial, spent + 1);
        opened.delete(bag.serial);
      }
    };
    return {
      look: () => siftContents(packContents(), {
        skipSerial: options.destSerial,
        opened,
        isLoose: options.wanted.has
      }),
      openNew: (bags) => {
        if (!OPEN_NESTED) {
          return false;
        }
        rearm(bags);
        return openNested(bags, opened, OPEN_DELAY);
      },
      wantedIn: (found) => movables(found, options.wanted)
    };
  };

  // src/stow/tally.ts
  var verdictFor = (issued, landedStacks) => issued === 0 ? "idle" : landedStacks > 0 ? "moved" : "quiet";
  var createQuiet = (max) => {
    let count = 0;
    return {
      saw: (verdict) => {
        if (verdict === "quiet") {
          count++;
        } else if (verdict === "moved") {
          count = 0;
        }
        return count;
      },
      // For the branches that were never the script's fault - a world save refuses every move it
      // catches, and counting those walks a run to its stop a save at a time
      reset: () => {
        count = 0;
      },
      reason: (left) => count >= max ? `${max} passes in a row moved nothing, with ${left} still in the pack` : void 0
    };
  };

  // src/stow/index.ts
  var NOTHING = { stacks: 0, items: 0 };
  var packSerial = player.backpack?.serial ?? die("stow: no backpack to watch");
  var picks = pickMany({
    prefix: "stow",
    prompt: "target one of each item to stow, ESC when done",
    maxPicks: MAX_PICKS,
    oplTimeout: OPL_TIMEOUT,
    keyOf: artKey,
    label: (picked) => `${picked.name || "unnamed"} ${artKey(picked)}`
  });
  for (const unknown of picks.filter((picked) => picked.graphic === 0)) {
    log(
      `stow: nothing knows the art of '${unknown.name}', so it cannot be matched - hover it and run again`
    );
  }
  var watched = picks.filter((picked) => picked.graphic !== 0);
  if (watched.length === 0) {
    die("stow: nothing to watch");
  }
  var destination = pickOne({
    prefix: "stow",
    prompt: "target the container to stow them in",
    oplTimeout: OPL_TIMEOUT
  }) ?? die("stow: nowhere to put it");
  if (destination.serial === packSerial) {
    die("stow: that is the backpack itself - pick a bag or a chest to stow into");
  }
  if (watched.some((picked) => picked.serial === destination.serial)) {
    die("stow: the container is one of the items to stow");
  }
  for (const bag of watched.filter((picked) => CONTAINER_GRAPHICS.has(picked.graphic))) {
    log(`stow: '${bag.name || "unnamed"}' ${artKey(bag)} is a container, so it goes across whole`);
  }
  var wanted = wantedFrom(watched);
  var scan = createScan({ destSerial: destination.serial, wanted });
  var quiet = createQuiet(MAX_QUIET_STOWS);
  var name = (picked) => `${picked.name || artKey(picked)} (${hex(picked.serial)})`;
  player.use(destination.serial);
  sleep(OPEN_DELAY);
  var here = () => {
    const found = client.findObject(destination.serial);
    return !!found && !isMobile(found);
  };
  log(
    `stow: watching ${watched.map((picked) => artKey(picked)).join(", ")} -> ${name(destination)}`
  );
  var stacks = 0;
  var items = 0;
  var lost = 0;
  var saidLost = false;
  var stop;
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (isSaving()) {
      waitOutSave();
      quiet.reset();
      continue;
    }
    if (!here()) {
      lost++;
      if (lost >= MAX_LOST_DEST) {
        stop = `${hex(destination.serial)} has not been where the client can see it for ${lost} polls`;
        break;
      }
      if (!saidLost) {
        saidLost = true;
        log(
          `stow: ${name(destination)} is not where the client can see it, waiting for it to come back`
        );
        heartbeat.resetBeat();
      }
      sleep(WATCH_POLL);
      continue;
    }
    if (saidLost) {
      saidLost = false;
      lost = 0;
      log(`stow: ${name(destination)} is back`);
      player.use(destination.serial);
      sleep(OPEN_DELAY);
      heartbeat.resetBeat();
    }
    const found = scan.look();
    if (!found.readable) {
      beat("waiting for the pack", cycle, items);
      sleep(WATCH_POLL);
      continue;
    }
    if (scan.openNew(found.containers)) {
      continue;
    }
    const todo = scan.wantedIn(found);
    if (LOG_EVERY_ITEM) {
      for (const item of todo) {
        log(`stow:   ${artKey(item)} x${item.amount ?? 1}`);
      }
    }
    const sent = issue(todo, destination.serial);
    const took = sent.length > 0 ? settle(sent, () => scan.wantedIn(scan.look())) : NOTHING;
    stacks += took.stacks;
    items += took.items;
    const verdict = verdictFor(sent.length, took.stacks);
    const misses = quiet.saw(verdict);
    if (verdict === "idle") {
      beat("watching", cycle, items);
      sleep(WATCH_POLL);
      continue;
    }
    if (verdict === "moved") {
      heartbeat.resetBeat();
      log(`stow: stowed ${took.items} in ${took.stacks} stacks, ${items} in total`);
      continue;
    }
    stop = quiet.reason(todo.length);
    if (stop) {
      break;
    }
    const backoff = backoffFor(misses, STOW_BACKOFF, STOW_BACKOFF_MAX);
    log(`stow: nothing moved (${misses}/${MAX_QUIET_STOWS}), waiting ${backoff / 1e3}s`);
    heartbeat.resetBeat();
    sleep(backoff);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(`stow: ${items} stowed in ${stacks} stacks`);
  log(`stow: stopping - ${reason}`);
  exit(`stow: ${reason}`);
})();
