"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var PACK_LIMIT = 120;
  var SAVE_WAIT = 6e4;
  var SAVE_POLL = 1e3;
  var SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"];
  var SAVING_TEXT = ["The world is saving", "Saving world", "World save started"];
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

  // src/arrows/config.ts
  var AMMO_GRAPHICS = [
    3903,
    // arrow
    7163
    // crossbow bolt
  ];
  var GRAB_RANGE = 2;
  var MOVE_DELAY = 250;
  var WATCH_POLL = 100;
  var SETTLE_TIMEOUT = 2e3;
  var SETTLE_POLL = 100;
  var MAX_QUIET_SWEEPS = 5;
  var SWEEP_BACKOFF = 1e3;
  var SWEEP_BACKOFF_MAX = 8e3;
  var WEIGHT_BUFFER = 20;

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var distanceTo = (spot) => Math.max(Math.abs(spot.x - player.x), Math.abs(spot.y - player.y));

  // src/arrows/floor.ts
  var GROUND = /* @__PURE__ */ new Set([0, 4294967295]);
  var parentOf = (item) => item.container >>> 0;
  var onGround = (item) => GROUND.has(parentOf(item));
  var ofType = (graphic) => client.findAllItemsOfType(graphic, void 0, "world");
  var onFloor = () => {
    const found = /* @__PURE__ */ new Map();
    for (const graphic of AMMO_GRAPHICS) {
      for (const item of ofType(graphic)) {
        if (item.graphic !== 0 && onGround(item)) {
          found.set(item.serial, item);
        }
      }
    }
    return [...found.values()];
  };
  var inReach = (items2, range) => items2.filter((item) => distanceTo(item) <= range);
  var describeFloor = () => AMMO_GRAPHICS.map((graphic) => {
    const found = ofType(graphic);
    if (found.length === 0) {
      return `${hex(graphic)} x0`;
    }
    const parents = [...new Set(found.map((item) => hex(parentOf(item))))];
    return `${hex(graphic)} x${found.length} (under ${parents.join(", ")})`;
  }).join(", ");
  var nearest = (items2) => items2.reduce(
    (best, item) => Math.min(distanceTo(item), best ?? Infinity),
    void 0
  );

  // src/arrows/grab.ts
  var sweep = (packSerial2, reachable) => {
    reachable.forEach((item, index) => {
      if (index > 0) {
        sleep(MOVE_DELAY);
      }
      player.moveItem(item.serial, packSerial2);
    });
  };
  var landed = (swept, after) => {
    const left = new Set(after.map((item) => item.serial));
    const gone = swept.filter((item) => !left.has(item.serial));
    return {
      stacks: gone.length,
      items: gone.reduce((total, item) => total + (item.amount ?? 1), 0)
    };
  };
  var settle = (swept, rescan) => {
    let took = landed(swept, rescan());
    for (let waited = 0; waited < SETTLE_TIMEOUT && took.stacks < swept.length; waited += SETTLE_POLL) {
      sleep(SETTLE_POLL);
      took = landed(swept, rescan());
    }
    return took;
  };

  // src/lib/containers.ts
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
      const reason2 = guard();
      if (reason2) {
        return reason2;
      }
    }
    return void 0;
  };

  // src/arrows/guards.ts
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

  // src/arrows/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "arrows",
    noun: "picked up",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

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

  // src/arrows/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    onDone: resetBeat
  });

  // src/arrows/index.ts
  var packSerial = player.backpack?.serial ?? die("arrows: no backpack to put them in");
  log(`arrows: watching within ${GRAB_RANGE} tiles - ${describeFloor()} in the world`);
  var stacks = 0;
  var items = 0;
  var quiet = 0;
  var saidOutOfReach = false;
  var stop;
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (isSaving()) {
      waitOutSave();
      quiet = 0;
      continue;
    }
    const reachable = inReach(onFloor(), GRAB_RANGE);
    if (reachable.length === 0) {
      const floor = onFloor();
      const closest = nearest(floor);
      if (closest !== void 0 && !saidOutOfReach) {
        saidOutOfReach = true;
        log(
          `arrows: ${floor.length} on the floor, nearest ${closest} tiles away - nothing within ${GRAB_RANGE}, so nothing to take`
        );
      }
      beat("watching", cycle, items);
      sleep(WATCH_POLL);
      continue;
    }
    sweep(packSerial, reachable);
    const took = settle(reachable, onFloor);
    stacks += took.stacks;
    items += took.items;
    if (took.stacks > 0) {
      quiet = 0;
      heartbeat.resetBeat();
      log(`arrows: took ${took.items} in ${took.stacks} stacks, ${items} in total`);
      continue;
    }
    quiet++;
    if (quiet >= MAX_QUIET_SWEEPS) {
      stop = `${MAX_QUIET_SWEEPS} sweeps in a row moved nothing, with ${reachable.length} in reach`;
      break;
    }
    const backoff = backoffFor(quiet, SWEEP_BACKOFF, SWEEP_BACKOFF_MAX);
    log(`arrows: nothing moved (${quiet}/${MAX_QUIET_SWEEPS}), waiting ${backoff / 1e3}s`);
    heartbeat.resetBeat();
    sleep(backoff);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(`arrows: ${items} picked up in ${stacks} stacks`);
  log(`arrows: stopping - ${reason}`);
  exit(`arrows: ${reason}`);
})();
