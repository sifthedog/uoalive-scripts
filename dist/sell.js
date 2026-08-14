"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/selling/config.ts
  var KEEP = 0;
  var MAX_PASSES = 10;
  var GUMP_TIMEOUT = 5e3;
  var SELL_DELAY = 1500;
  var SALE_TIMEOUT = 3e3;
  var SALE_POLL = 200;
  var OPL_TIMEOUT = 2e3;
  var HOIST_FROM_BAGS = true;
  var MOVE_DELAY = 600;
  var OPEN_DELAY = 800;
  var MAX_HOIST_PASSES = 5;

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

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;

  // src/selling/hoist.ts
  var nameOf = (item) => {
    const known = (item.name ?? "").trim();
    return known || (client.queryItemOPL(item.serial, OPL_TIMEOUT)?.name ?? "").trim();
  };
  var nestedMatches = (name) => {
    const contents = player.backpack?.contents;
    const topLevel = new Set((contents ?? []).map((item) => item.serial));
    const wanted = name.toLowerCase();
    return collectIn(
      contents,
      (item) => !topLevel.has(item.serial) && nameOf(item).toLowerCase() === wanted
    );
  };
  var looseMatches = (name) => {
    const wanted = name.toLowerCase();
    return (player.backpack?.contents ?? []).filter((item) => nameOf(item).toLowerCase() === wanted);
  };
  var openUnopened = (opened) => {
    const containers = collectIn(player.backpack?.contents, isContainer).filter(
      (container) => !opened.has(container.serial)
    );
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
    log("sell: target the item you want to sell");
    const info = target.query();
    const serial = info?.serial ?? 0;
    if (!serial) {
      log("sell: nothing targeted", info);
      return void 0;
    }
    const name = resolveName(serial);
    if (!name) {
      log(`sell: no name for ${hex(serial)}, the vendor list can only be matched by name`);
      return void 0;
    }
    return { serial, name };
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
  var looseTotal = (serials) => (player.backpack?.contents ?? []).filter((item) => serials.has(item.serial)).reduce((sum, item) => sum + (item.amount ?? 1), 0);
  var waitForSale = (offered, timeoutMs, pollMs) => {
    const serials = new Set(offered.map((item) => item.serial));
    const total = offered.reduce((sum, item) => sum + item.amount, 0);
    let remaining = total;
    for (let waited = 0; waited < timeoutMs && remaining > 0; waited += pollMs) {
      sleep(pollMs);
      remaining = looseTotal(serials);
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
        const names = [...new Set(data.items.map((item) => item.name))];
        log(`sell: no '${name}' on offer. Vendor listed: ${names.join(", ")}`);
        break;
      }
      const toSell = withKeepBack2(matches);
      if (toSell.length === 0) {
        log(`sell: ${amountOf(looseMatches(name))} left, keeping them back`);
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
      const left = amountOf(looseMatches(name));
      if (left <= KEEP) {
        break;
      }
      sleep(SELL_DELAY);
    }
    return sold2;
  };

  // src/selling/index.ts
  var picked = pickItem() ?? die("sell: nothing to sell");
  log(`sell: selling '${picked.name}'`);
  if (HOIST_FROM_BAGS) {
    hoistToPack(picked.name);
  }
  var sold = sellAll(picked.name);
  log(`sell: ${sold} x '${picked.name}' sold`);
})();
