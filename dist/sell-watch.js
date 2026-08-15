"use strict";
(() => {
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

  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

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

  // src/lib/clock.ts
  var now = () => Date.now();

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

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);

  // src/lib/pack.ts
  var totalMatching = (matches, contents = packContents()) => (contents ?? []).reduce(
    (total, item) => total + (matches(item) ? item.amount ?? 1 : 0) + totalMatching(matches, contentsOf(item) ?? []),
    0
  );

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;

  // src/selling/config.ts
  var KEEP = 0;
  var MAX_PASSES = 10;
  var GUMP_TIMEOUT = 5e3;
  var SELL_DELAY = 1500;
  var SALE_TIMEOUT = 3e3;
  var SALE_POLL = 200;
  var OPL_TIMEOUT = 2e3;
  var HOIST_FROM_BAGS = false;
  var MOVE_DELAY = 600;
  var OPEN_DELAY = 800;
  var MAX_HOIST_PASSES = 5;
  var SELL_AT = 30;
  var SELL_AT_SLOTS = 110;
  var WATCH_POLL = 5e3;
  var WATCH_BACKOFF = 1e4;
  var WATCH_BACKOFF_MAX = 12e4;
  var MAX_QUIET_SALES = 5;

  // src/selling/hoist.ts
  var names = /* @__PURE__ */ new Map();
  var oplAnswersNames = true;
  var misses = 0;
  var nameOf = (item) => {
    const known = (item.name ?? "").trim();
    if (known) {
      return known;
    }
    const cached = names.get(item.serial);
    if (cached !== void 0) {
      return cached;
    }
    if (!oplAnswersNames) {
      return "";
    }
    const fromTooltip = (client.queryItemOPL(item.serial, OPL_TIMEOUT)?.name ?? "").trim();
    names.set(item.serial, fromTooltip);
    misses = fromTooltip ? 0 : misses + 1;
    if (misses >= 3) {
      oplAnswersNames = false;
      log("sell: tooltips are not answering here, so only items the client has already named can match");
    }
    return fromTooltip;
  };
  var nestedMatches = (name) => {
    const contents = packContents();
    const topLevel = new Set((contents ?? []).map((item) => item.serial));
    const wanted = name.toLowerCase();
    return collectIn(
      contents,
      (item) => !topLevel.has(item.serial) && nameOf(item).toLowerCase() === wanted
    );
  };
  var sellableMatches = (name) => {
    const wanted = name.toLowerCase();
    return collectIn(packContents(), (item) => nameOf(item).toLowerCase() === wanted);
  };
  var CONTAINER_WORDS = /\b(bag|pouch|box|chest|crate|basket|backpack)\b/i;
  var unlisted = /* @__PURE__ */ new Set();
  var warnIfContainerish = (item) => {
    const name = (item.name ?? "").trim();
    if (!CONTAINER_WORDS.test(name) || unlisted.has(item.serial)) {
      return;
    }
    unlisted.add(item.serial);
    log(
      `sell: '${name}' (${hex(item.serial)}) reads like a container, but its graphic ${hex(item.graphic)} is not in CONTAINER_GRAPHICS, so it will not be opened`
    );
  };
  var openUnopened = (opened) => {
    const everything = collectIn(packContents(), () => true);
    const containers = [];
    for (const item of everything) {
      if (!isContainer(item)) {
        warnIfContainerish(item);
        continue;
      }
      if (!opened.has(item.serial)) {
        containers.push(item);
      }
    }
    for (const container of containers) {
      player.use(container.serial);
      opened.add(container.serial);
      sleep(OPEN_DELAY);
    }
    return containers.length > 0;
  };
  var hoistToPack = (name) => {
    const packSerial = player.backpack?.serial;
    if (!packSerial) {
      log("sell: no backpack to move anything into");
      return 0;
    }
    const opened = /* @__PURE__ */ new Set();
    const attempted = /* @__PURE__ */ new Set();
    let moved = 0;
    for (let pass = 0; pass < MAX_HOIST_PASSES; pass++) {
      const openedAny = openUnopened(opened);
      const fresh = nestedMatches(name).filter((item) => !attempted.has(item.serial));
      if (fresh.length === 0 && !openedAny) {
        break;
      }
      for (const item of fresh) {
        player.moveItem(item.serial, packSerial);
        attempted.add(item.serial);
        moved++;
        sleep(MOVE_DELAY);
      }
    }
    if (moved > 0) {
      log(`sell: moved ${moved} x '${name}' out of bags so the vendor can see them`);
    }
    return moved;
  };

  // src/selling/pick.ts
  var resolveName = (serial) => {
    const fromTooltip = (client.queryItemOPL(serial, OPL_TIMEOUT)?.name ?? "").trim();
    return fromTooltip || (client.findObject(serial)?.name ?? "").trim();
  };
  var pickItem = () => {
    target.cancel();
    log("sell: target the item you want to sell");
    const info = target.query();
    const serial = info?.serial ?? 0;
    if (!serial) {
      target.cancel();
      log("sell: nothing targeted", info);
      return void 0;
    }
    const name = resolveName(serial);
    if (!name) {
      log(`sell: no name for ${hex(serial)}, the vendor list can only be matched by name`);
      return void 0;
    }
    const graphic = info?.graphic ?? client.findObject(serial)?.graphic ?? 0;
    return { serial, name, graphic };
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
  var packTotal = (serials) => collectIn(packContents(), (item) => serials.has(item.serial)).reduce(
    (sum, item) => sum + (item.amount ?? 1),
    0
  );
  var waitForSale = (offered, timeoutMs, pollMs) => {
    const serials = new Set(offered.map((item) => item.serial));
    const total = offered.reduce((sum, item) => sum + item.amount, 0);
    let remaining = total;
    for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
      sleep(pollMs);
      remaining = packTotal(serials);
    }
    return total - remaining;
  };
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

  // src/selling/offer.ts
  var withKeepBack2 = (matches) => withKeepBack(matches, KEEP);

  // src/selling/sell.ts
  var amountOf = (items) => items.reduce((sum, item) => sum + (item.amount ?? 1), 0);
  var sellAll = (name) => {
    const nameMatches = namedExactly(name);
    let sold2 = 0;
    for (let pass = 0; pass < MAX_PASSES; pass++) {
      const data = openSellGump("sell", GUMP_TIMEOUT);
      if (!data) {
        break;
      }
      const matches = data.items.filter(nameMatches);
      if (matches.length === 0) {
        const names2 = [...new Set(data.items.map((item) => item.name))];
        log(`sell: no '${name}' on offer. Vendor listed: ${names2.join(", ")}`);
        break;
      }
      const toSell = withKeepBack2(matches);
      if (toSell.length === 0) {
        log(`sell: ${amountOf(sellableMatches(name))} left, keeping them back`);
        break;
      }
      const offered = toSell.reduce((sum, item) => sum + item.amount, 0);
      client.sendSellRequest(data.vendor, toSell);
      const taken = waitForSale(toSell, SALE_TIMEOUT, SALE_POLL);
      sold2 += taken;
      log(`sell: pass ${pass + 1}, offered ${offered} x ${name}, vendor took ${taken}`);
      if (taken === 0) {
        log(`sell: stalled with ${offered} left, vendor is not taking them`);
        break;
      }
      const left = amountOf(sellableMatches(name));
      if (left <= KEEP) {
        break;
      }
      sleep(SELL_DELAY);
    }
    return sold2;
  };

  // src/selling/trigger.ts
  var reasonToSell = (held2, slots2) => {
    if (held2 >= SELL_AT) {
      return `${held2} held`;
    }
    if (slots2 >= SELL_AT_SLOTS && held2 > 0) {
      return `${slots2} pack slots used`;
    }
    return void 0;
  };

  // src/selling/watch.ts
  var picked = pickItem() ?? die("sell-watch: nothing to watch");
  var isWatched = (item) => item.graphic === picked.graphic;
  var held = () => totalMatching(isWatched);
  var slots = () => (packContents() ?? []).length;
  var heartbeat = createHeartbeat({
    prefix: "sell-watch",
    noun: "sold",
    everyMs: HEARTBEAT_EVERY
  });
  var quiet = 0;
  var sold = 0;
  var stop;
  log(
    `sell-watch: watching for ${SELL_AT} x '${picked.name}' ${hex(picked.graphic)} (or ${SELL_AT_SLOTS} pack slots), ${held()} held`
  );
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = firstReason(dead);
    if (stop) {
      break;
    }
    const inPack = held();
    const due = reasonToSell(inPack, slots());
    if (!due) {
      heartbeat.beat("watching", cycle, sold);
      sleep(WATCH_POLL);
      continue;
    }
    log(`sell-watch: ${due} - selling '${picked.name}'`);
    if (HOIST_FROM_BAGS) {
      hoistToPack(picked.name);
    }
    const took = sellAll(picked.name);
    sold += took;
    if (took > 0) {
      quiet = 0;
      heartbeat.resetBeat();
      log(`sell-watch: sold ${took}, ${held()} left, ${sold} sold in total`);
      sleep(WATCH_POLL);
      continue;
    }
    quiet++;
    if (quiet >= MAX_QUIET_SALES) {
      stop = `${MAX_QUIET_SALES} sales in a row took nothing, with ${inPack} x '${picked.name}' still in the pack`;
      break;
    }
    const backoff = backoffFor(quiet, WATCH_BACKOFF, WATCH_BACKOFF_MAX);
    log(`sell-watch: nothing sold (${quiet}/${MAX_QUIET_SALES}), waiting ${backoff / 1e3}s`);
    heartbeat.resetBeat();
    sleep(backoff);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(`sell-watch: ${sold} x '${picked.name}' sold, ${held()} still in the pack`);
  log(`sell-watch: stopping - ${reason}`);
  exit(`sell-watch: ${reason}`);
})();
