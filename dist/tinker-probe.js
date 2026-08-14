"use strict";
(() => {
  // src/lib/arts.ts
  var INGOT_GRAPHICS = /* @__PURE__ */ new Set([7151, 7152, 7153, 7154]);

  // src/tinkering/config.ts
  var TOOL_NAME = "tool kit";
  var TOOL_GRAPHICS = /* @__PURE__ */ new Set([7864, 7868]);
  var SPARE_BAG_SERIAL = void 0;
  var INGOT_HUE = 0;
  var GUMP_SERIAL = 3449376977;
  var CATEGORIES = {
    jewelry: 1,
    woodenItems: 21,
    tools: 41,
    parts: 61,
    utensils: 81,
    miscellaneous: 101,
    assemblies: 121,
    traps: 141,
    magicJewelry: 161
  };
  var RECIPES = {
    lockpicks: { label: "lockpick", category: CATEGORIES.tools, nextPages: 0, item: void 0 },
    rings: { label: "ring", category: CATEGORIES.jewelry, nextPages: 0, item: void 0 }
  };
  var OUTCOME_TEXT = {
    success: ["You create the item", "You create an exceptional quality item"],
    failed: ["You failed to create the item"],
    noMaterial: ["You do not have sufficient metal", "lack the required materials"],
    wornOut: ["You have worn out your tool"],
    throttled: ["You must wait"]
  };
  var STEP_DELAY = 400;
  var GUMP_TIMEOUT = 5e3;
  var GUMP_POLL = 200;
  var CRAFT_TIMEOUT = 8e3;
  var PROBE_MAX_BUTTON = 600;
  var PROBE_MAX_CATEGORIES = 12;
  var LOCKPICK_GRAPHIC = 5372;
  var PROBE_PAGES = false;
  var PROBE_MAX_PAGES = 12;
  var PROBE_TRIAL_PATH = [];
  var PROBE_TRIAL_BUTTONS = [1, 2, 3, 7, 21, 22, 23, 41, 42, 43, 61, 62, 63];
  var PROBE_MAX_TRIALS = 13;
  var PROBE_TRIAL_DELAY = 2500;
  var PROBE_ANNOUNCE = true;
  var PROBE_WALK = false;
  var PROBE_KEYWORDS = [
    "tinker",
    "tools",
    "parts",
    "utensils",
    "assemblies",
    "jewelry",
    "traps",
    "wooden",
    "miscellaneous",
    "lockpick",
    "ring"
  ];
  var PROBE_MODE = "scan";

  // src/tinkering/gump.ts
  var SERIALS = GUMP_SERIAL === void 0 ? [] : [.../* @__PURE__ */ new Set([GUMP_SERIAL >>> 0, GUMP_SERIAL | 0])];
  var craftGump = () => {
    for (const serial of SERIALS) {
      if (Gump.exists(serial)) {
        const found = Gump.findOrWait(serial, GUMP_POLL);
        if (found) {
          return found;
        }
      }
    }
    const last = Gump.last;
    return last && last.exists ? last : void 0;
  };
  var pageWith = (buttonID, timeout) => {
    for (let waited = 0; waited <= timeout; waited += GUMP_POLL) {
      const gump2 = craftGump();
      if (gump2 && gump2.hasButton(buttonID)) {
        return gump2;
      }
      sleep(GUMP_POLL);
    }
    return void 0;
  };
  var openCraftGump = (toolSerial2, categoryButton) => {
    const alreadyOpen = pageWith(categoryButton, 0);
    if (alreadyOpen) {
      return alreadyOpen;
    }
    player.use(toolSerial2);
    return pageWith(categoryButton, GUMP_TIMEOUT);
  };
  var backToCategories = (toolSerial2, categoryButton) => {
    craftGump()?.close();
    sleep(GUMP_POLL);
    return openCraftGump(toolSerial2, categoryButton);
  };

  // src/tinkering/ingots.ts
  var isIngot = (item) => INGOT_GRAPHICS.has(item.graphic) && (item.hue ?? 0) === INGOT_HUE;
  var totalIn = (contents) => (contents ?? []).reduce(
    (total, item) => total + (isIngot(item) ? item.amount ?? 1 : 0) + totalIn(item.contents),
    0
  );
  var ingotTotal = (contents = player.backpack?.contents) => totalIn(contents);

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

  // src/tinkering/tool.ts
  var toolGraphic;
  var spareBagSerial = SPARE_BAG_SERIAL;
  var isTool = (item) => toolGraphic !== void 0 && item.graphic === toolGraphic || TOOL_GRAPHICS.has(item.graphic) || (item.name ?? "").toLowerCase().includes(TOOL_NAME);
  var rememberTool = (item) => {
    if (item && toolGraphic === void 0) {
      toolGraphic = item.graphic;
      log(`tool: tinker's tools graphic is 0x${item.graphic.toString(16)}`);
    }
  };
  var toolAlive = (serial) => serial !== void 0 && !!client.findObject(serial);
  var findTool = () => {
    let tool = findIn(player.backpack?.contents, isTool);
    if (!tool && openContainers(spareBagSerial)) {
      tool = findIn(player.backpack?.contents, isTool);
    }
    if (!tool) {
      const graphics = (player.backpack?.contents ?? []).map((item) => `0x${item.graphic.toString(16)}`).join(", ");
      log(`tool: no tinker's tools left. Top level of pack holds: ${graphics}`);
      return void 0;
    }
    rememberTool(tool);
    if (tool.container && tool.container !== player.backpack?.serial) {
      spareBagSerial = tool.container;
    }
    return tool.serial;
  };

  // src/tinkering/craft.ts
  var ALL_OUTCOME_TEXT = Object.values(OUTCOME_TEXT).flat();
  var outcomeFor = (matched) => Object.keys(OUTCOME_TEXT).find((name) => OUTCOME_TEXT[name].includes(matched));

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
  var describeDiff = (changes) => changes.length ? changes.map(({ key, delta }) => `${key} ${delta > 0 ? "+" : ""}${delta}`).join(", ") : "no change";

  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/tinkering/probe.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  log("probe: pack contents (graphic / hue / amount / name)");
  for (const item of player.backpack?.contents ?? []) {
    log(`probe:   ${hex(item.graphic)} hue ${item.hue ?? 0} x${item.amount ?? 1} "${item.name ?? ""}"`);
  }
  var skill = player.getSkill(Skills.Tinkering);
  log(`probe: tinkering base ${skill?.base}, value ${skill?.value}`);
  var baselineIngots = ingotTotal();
  log(`probe: ${baselineIngots} ingots matched by INGOT_GRAPHICS + INGOT_HUE`);
  var toolSerial = findTool();
  if (!toolSerial) {
    die("probe: no tinker's tools in the pack");
  }
  var acquireGump = () => {
    journal.clear();
    player.use(toolSerial);
    let reported = "";
    for (let waited = GUMP_POLL; waited <= GUMP_TIMEOUT; waited += GUMP_POLL) {
      sleep(GUMP_POLL);
      const last = Gump.last;
      const found = craftGump();
      const state = `lastSerial=${hex(Gump.lastSerial)} exists=${Gump.exists(Gump.lastSerial)} last=${last ? "set" : "null"} resolved=${found ? "yes" : "no"}`;
      if (state !== reported) {
        log(`probe:   +${waited}ms ${state}`);
        reported = state;
      }
      if (found) {
        return found;
      }
    }
    log(`probe: nothing from Gump.last after ${GUMP_TIMEOUT}ms, trying the fallbacks`);
    for (const text of ["tinker", "tinkering", "craft", "selection menu"]) {
      const found = Gump.findOrWait(text, 1e3);
      if (found) {
        log(`probe: found it by text "${text}"`);
        return found;
      }
    }
    if (Gump.lastSerial) {
      const local = Gump.findOrWait(Gump.lastSerial, 1e3, false);
      if (local) {
        log("probe: found it as a LOCAL gump - set fromServer false when opening it");
        return local;
      }
    }
    const refusal = journal.waitForTextAny(
      ["must be in your backpack", "cannot use", "must wait", "What do you want", "do not have"],
      void 0,
      500
    );
    if (refusal) {
      log(`probe: the shard said "${refusal}" - that is why there is no menu`);
    }
    return void 0;
  };
  var gump = acquireGump();
  if (!gump) {
    log(`probe: no menu from tool ${hex(toolSerial)} (graphic 0x1eb8 "Tool Kit")`);
    log("probe: if lastSerial stayed 0x0 the shard sent no gump at all - try double-clicking the");
    log("probe: tools by hand to confirm the menu opens, and say what it looks like.");
    die("probe: could not acquire the tinkering menu");
  }
  log(`probe: craft gump serial is ${hex(Gump.lastSerial)}  <- GUMP_SERIAL`);
  var scan = (page) => {
    const found = [];
    for (let id = 0; id <= PROBE_MAX_BUTTON; id++) {
      if (page.hasButton(id)) {
        found.push(id);
      }
    }
    return found;
  };
  var keywords = (page, where) => {
    const hits = PROBE_KEYWORDS.filter((word) => page.containsText(word));
    log(`probe: ${where} containsText hits: ${hits.length ? hits.join(", ") : "NONE"}`);
  };
  var logIDs = (label, ids) => {
    if (ids.length === 0) {
      log(`probe: ${label}: none`);
      return;
    }
    log(`probe: ${label} (${ids.length}):`);
    for (let start = 0; start < ids.length; start += 24) {
      log(`probe:   ${ids.slice(start, start + 24).join(" ")}`);
    }
  };
  var categoryButtons = scan(gump);
  logIDs("buttons on the page as opened", categoryButtons);
  keywords(gump, "as opened");
  log("probe: containsText spans the whole gump, so it cannot identify a page - using buttons only");
  var sameIDs = (a, b) => a.length === b.length && a.every((id, i) => id === b[i]);
  var paged = false;
  var previous = categoryButtons;
  for (let page = 1; PROBE_PAGES && page <= PROBE_MAX_PAGES; page++) {
    gump.switchPage(page);
    sleep(GUMP_POLL);
    const here = craftGump();
    if (!here || !here.exists) {
      log(`probe: gump closed while switching to page ${page}`);
      break;
    }
    const ids = scan(here);
    if (page > 1 && sameIDs(ids, previous)) {
      log(`probe: page ${page} is identical to page ${page - 1}, so that was the last one`);
      break;
    }
    logIDs(`page ${page}${sameIDs(ids, categoryButtons) ? " (same as opened)" : ""}`, ids);
    if (!sameIDs(ids, categoryButtons)) {
      paged = true;
    }
    previous = ids;
  }
  if (PROBE_PAGES) {
    log(`probe: switchPage ${paged ? "CHANGES the button set - this is one paged gump" : "changes nothing - pages are not how it navigates"}`);
  }
  var strideFor = (ids) => {
    const bases = ids.filter((id) => id > 0);
    for (const stride of [20, 7, 10, 25, 100]) {
      const offsets = new Set(bases.map((id) => (id - 1) % stride));
      if (offsets.size <= 4) {
        return { stride, offsets: [...offsets].sort((a, b) => a - b) };
      }
    }
    return void 0;
  };
  var shape = strideFor(categoryButtons);
  if (shape) {
    const groups = new Set(categoryButtons.filter((id) => id > 0).map((id) => Math.floor((id - 1) / shape.stride)));
    log(`probe: numbering fits id = 1 + offset + ${shape.stride} * group`);
    log(`probe:   ${groups.size} groups, offsets used: ${shape.offsets.join(", ")}`);
  }
  if (gump.hasButton(2)) {
    log("probe: button 2 already exists here, so the RunUO-shaped walk cannot tell pages apart");
  }
  var categories = PROBE_WALK ? categoryButtons.filter((id) => id > 0 && (id - 1) % 7 === 0).slice(0, PROBE_MAX_CATEGORIES) : [];
  if (!PROBE_WALK) {
    log("probe: PROBE_WALK is off, so no button was pressed. Send the lists above.");
  }
  for (const category of categories) {
    const page = openCraftGump(toolSerial, category);
    if (!page) {
      log(`probe: category page gone before ${category}, stopping the walk`);
      break;
    }
    page.reply(category);
    const itemPage = pageWith(2, GUMP_TIMEOUT);
    if (!itemPage) {
      log(`probe: category ${category} opened nothing with an item button on it`);
      backToCategories(toolSerial, category);
      continue;
    }
    const items = scan(itemPage).filter((id) => (id - 1) % 7 === 1);
    log(`probe: category ${category} -> ${items.length} items: ${items.join(", ")}`);
    keywords(itemPage, `category ${category}`);
    if (ingotTotal() < baselineIngots) {
      die(`probe: ingots dropped after pressing ${category} - that press crafted something, stopping`);
    }
    backToCategories(toolSerial, category);
    sleep(STEP_DELAY);
  }
  log(`probe: put ${hex(Gump.lastSerial)} in GUMP_SERIAL.`);
  if (PROBE_WALK) {
    log("probe: item #N on a category page is button 2 + (N - 1) * 7, counted top to bottom.");
    log('probe: careful - "ring" also matches "springs" and "earrings". Trust the jewelry hit.');
  } else {
    log("probe: also say how the menu looks by hand - one window listing everything, or a");
    log("probe: category list you click into - and where lockpick and ring sit in it.");
  }
  if (PROBE_MODE === "trial") {
    const walkTo = (announce) => {
      if (PROBE_TRIAL_PATH.length) {
        craftGump()?.close();
        sleep(GUMP_POLL);
      }
      let page = craftGump();
      for (let attempt = 0; !page && attempt < 2; attempt++) {
        player.use(toolSerial);
        page = pageWith(PROBE_TRIAL_PATH[0] ?? 1, GUMP_TIMEOUT) ?? craftGump();
      }
      if (!page) {
        log(`probe: gump did not reopen (lastSerial ${hex(Gump.lastSerial)}, exists ${Gump.exists(Gump.lastSerial)})`);
        return void 0;
      }
      for (const step of PROBE_TRIAL_PATH) {
        page.reply(step);
        sleep(PROBE_TRIAL_DELAY);
        const landed2 = craftGump();
        if (!landed2) {
          return void 0;
        }
        page = landed2;
        if (announce) {
          logIDs(`buttons after ${step}`, scan(page));
        }
      }
      return page;
    };
    const landed = walkTo(true);
    if (!landed) {
      die(
        PROBE_TRIAL_PATH.length ? `probe: could not walk the path ${PROBE_TRIAL_PATH.join(" -> ")}` : "probe: the menu was not open and would not reopen"
      );
    }
    const candidates = (PROBE_TRIAL_BUTTONS.length ? PROBE_TRIAL_BUTTONS : scan(landed).filter((id) => (id - 2) % 20 === 0)).slice(0, PROBE_MAX_TRIALS);
    log(`probe: trialling ${candidates.length} buttons: ${candidates.join(" ")}`);
    for (const id of candidates) {
      const open = walkTo(false);
      if (!open) {
        log(`probe: could not get back to the start before ${id}, stopping`);
        break;
      }
      const buttonsBefore = scan(open);
      const packBefore = countsByGraphic();
      if (PROBE_ANNOUNCE) {
        client.headMsg(`btn ${id}`, player, 66);
        sleep(600);
      }
      open.reply(id);
      sleep(PROBE_TRIAL_DELAY);
      target.cancel();
      const after = craftGump();
      const changes = describeDiff(diffCounts(packBefore, countsByGraphic()));
      const navigated = after ? !sameIDs(scan(after), buttonsBefore) : false;
      log(`probe: ${id} -> pack: ${changes}${after ? navigated ? " | NAVIGATED" : "" : " | GUMP CLOSED"}`);
      if (changes.includes(`0x${LOCKPICK_GRAPHIC.toString(16)}`)) {
        log(`probe: *** ${id} is the lockpick button - put it in RECIPES.lockpicks.item ***`);
        break;
      }
    }
  }
  if (PROBE_MODE === "outcome") {
    const recipe = RECIPES.lockpicks;
    if (recipe.category === void 0 || recipe.item === void 0) {
      die("probe: outcome mode needs RECIPES.lockpicks filled in first");
    }
    const categoryPage = openCraftGump(toolSerial, recipe.category);
    if (!categoryPage) {
      die("probe: outcome mode could not open the category page");
    }
    categoryPage.reply(recipe.category);
    const itemPage = pageWith(recipe.item, GUMP_TIMEOUT);
    if (!itemPage) {
      die(`probe: outcome mode found no button ${recipe.item} - RECIPES.lockpicks.item is wrong`);
    }
    const before = ingotTotal();
    journal.clear();
    log(`probe: outcome mode crafting one ${recipe.label}`);
    itemPage.reply(recipe.item);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CRAFT_TIMEOUT);
    log(`probe: journal matched ${matched ? `"${matched}" -> ${outcomeFor(matched)}` : "NOTHING"}`);
    const after = craftGump();
    for (const [name, strings] of Object.entries(OUTCOME_TEXT)) {
      const inGump = strings.filter((text) => after?.containsText(text));
      if (inGump.length) {
        log(`probe: the returned gump contains the ${name} text: ${inGump.join(", ")}`);
      }
    }
    log(`probe: ingots ${before} -> ${ingotTotal()}, tool still exists: ${toolAlive(toolSerial)}`);
  }
})();
