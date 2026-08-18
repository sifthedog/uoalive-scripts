"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;

  // src/selling/config.ts
  var KEEP = 0;
  var MAX_PASSES = 10;
  var MAX_PICKS = 20;
  var GUMP_TIMEOUT = 5e3;
  var SELL_DELAY = 1500;
  var SALE_TIMEOUT = 3e3;
  var SALE_POLL = 200;
  var OPL_TIMEOUT = 2e3;
  var HOIST_FROM_BAGS = false;
  var MOVE_DELAY = 600;
  var OPEN_DELAY = 800;
  var MAX_HOIST_PASSES = 5;

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
  var describe = (prefix, info) => {
    const serial = info.serial ?? 0;
    const name = resolveName(serial);
    if (!name) {
      log(`${prefix}: no name for ${hex(serial)}, the vendor list can only be matched by name`);
      return void 0;
    }
    const graphic = info.graphic ?? client.findObject(serial)?.graphic ?? 0;
    return { serial, name, graphic };
  };
  var pickItems = (prefix) => {
    const picks = [];
    const seen = /* @__PURE__ */ new Set();
    log(`${prefix}: target the items you want to sell, ESC when done`);
    let asked = 0;
    for (; asked < MAX_PICKS; asked++) {
      const info = clicked(prefix);
      if (!info) {
        break;
      }
      const picked2 = describe(prefix, info);
      if (!picked2) {
        continue;
      }
      const name = picked2.name.toLowerCase();
      if (seen.has(name)) {
        log(`${prefix}: '${picked2.name}' is already on the list`);
        continue;
      }
      seen.add(name);
      picks.push(picked2);
      log(`${prefix}:   ${picks.length}. ${picked2.name}`);
    }
    if (asked === MAX_PICKS) {
      log(`${prefix}: ${MAX_PICKS} clicks is as many as one run takes`);
      target.cancel();
    }
    return picks;
  };

  // src/lib/vendor.ts
  var namedAnyOf = (names3) => {
    const wanted = new Set(names3.map((name) => name.toLowerCase()));
    return (entry) => wanted.has((entry.name ?? "").toLowerCase());
  };
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
  var packLeft = (serials) => {
    const left = /* @__PURE__ */ new Map();
    for (const item of collectIn(packContents(), (held) => serials.has(held.serial))) {
      left.set(item.serial, (left.get(item.serial) ?? 0) + (item.amount ?? 1));
    }
    return left;
  };
  var waitForSaleBySerial = (offered, timeoutMs, pollMs) => {
    const serials = new Set(offered.map((item) => item.serial));
    let left = /* @__PURE__ */ new Map();
    let remaining = offered.reduce((sum, item) => sum + item.amount, 0);
    for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
      sleep(pollMs);
      left = packLeft(serials);
      remaining = [...left.values()].reduce((sum, amount) => sum + amount, 0);
    }
    return new Map(
      offered.map((item) => [item.serial, Math.max(0, item.amount - (left.get(item.serial) ?? 0))])
    );
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
  var withKeepBack2 = (matches) => {
    const byName = /* @__PURE__ */ new Map();
    for (const entry of matches) {
      const name = (entry.name ?? "").toLowerCase();
      const group = byName.get(name);
      if (group) {
        group.push(entry);
        continue;
      }
      byName.set(name, [entry]);
    }
    const order = new Map(matches.map((entry, index) => [entry.serial, index]));
    return [...byName.values()].flatMap((group) => withKeepBack(group, KEEP)).sort((a, b) => (order.get(a.serial) ?? 0) - (order.get(b.serial) ?? 0));
  };

  // src/selling/sell.ts
  var amountOf = (items) => items.reduce((sum, item) => sum + (item.amount ?? 1), 0);
  var describeCounts = (counts) => [...counts].filter(([, amount]) => amount > 0).map(([name, amount]) => `${amount} x '${name}'`).join(", ");
  var totalOfCounts = (counts) => [...counts.values()].reduce((sum, amount) => sum + amount, 0);
  var stillHeld = (names3) => new Map(names3.map((name) => [name, amountOf(sellableMatches(name))]));
  var sellAll = (names3) => {
    const wanted = namedAnyOf(names3);
    const byName = new Map(names3.map((name) => [name, 0]));
    const asPicked = new Map(names3.map((name) => [name.toLowerCase(), name]));
    const nameOf2 = (entry) => asPicked.get((entry.name ?? "").toLowerCase()) ?? (entry.name ?? "");
    let total = 0;
    for (let pass = 0; pass < MAX_PASSES; pass++) {
      const data = openSellGump("sell", GUMP_TIMEOUT);
      if (!data) {
        break;
      }
      const matches = data.items.filter(wanted);
      if (matches.length === 0) {
        const listed = [...new Set(data.items.map((item) => item.name))];
        log(`sell: nothing of ${names3.join(", ")} on offer. Vendor listed: ${listed.join(", ")}`);
        break;
      }
      const toSell = withKeepBack2(matches);
      if (toSell.length === 0) {
        log(`sell: ${describeCounts(stillHeld(names3))} left, keeping them back`);
        break;
      }
      const named = new Map(matches.map((entry) => [entry.serial, nameOf2(entry)]));
      const offered = /* @__PURE__ */ new Map();
      for (const item of toSell) {
        const name = named.get(item.serial) ?? "";
        offered.set(name, (offered.get(name) ?? 0) + item.amount);
      }
      client.sendSellRequest(data.vendor, toSell);
      const taken = waitForSaleBySerial(toSell, SALE_TIMEOUT, SALE_POLL);
      const tookByName = /* @__PURE__ */ new Map();
      for (const [serial, amount] of taken) {
        const name = named.get(serial) ?? "";
        tookByName.set(name, (tookByName.get(name) ?? 0) + amount);
        byName.set(name, (byName.get(name) ?? 0) + amount);
      }
      const took = totalOfCounts(tookByName);
      total += took;
      log(
        `sell: pass ${pass + 1}, offered ${describeCounts(offered)}, vendor took ${describeCounts(tookByName) || "nothing"}`
      );
      if (took === 0) {
        log(`sell: stalled with ${totalOfCounts(offered)} left, vendor is not taking them`);
        break;
      }
      if ([...stillHeld(names3).values()].every((held) => held <= KEEP)) {
        break;
      }
      sleep(SELL_DELAY);
    }
    return { total, byName };
  };

  // src/selling/index.ts
  var picked = pickItems("sell");
  if (picked.length === 0) {
    die("sell: nothing to sell");
  }
  var names2 = picked.map((item) => item.name);
  log(`sell: selling ${names2.map((name) => `'${name}'`).join(", ")}`);
  if (HOIST_FROM_BAGS) {
    for (const name of names2) {
      hoistToPack(name);
    }
  }
  var sold = sellAll(names2);
  log(`sell: ${describeCounts(sold.byName) || "nothing"} sold, ${sold.total} in all`);
})();
