"use strict";
(() => {
  // src/lib/arts.ts
  var INGOT_GRAPHICS = /* @__PURE__ */ new Set([7151, 7152, 7153, 7154]);

  // src/tinkering/config.ts
  var TOOL_NAME = "tool kit";
  var TOOL_GRAPHICS = /* @__PURE__ */ new Set([7864, 7868]);
  var SPARE_BAG_SERIAL = void 0;
  var INGOT_HUE = 0;
  var LOCKPICK_FROM = 450;
  var RING_FROM = 950;
  var STOP_AT = 1e3;
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
  var NEXT_PAGE_BUTTON = void 0;
  var isCalibrated = (recipe) => recipe.item !== void 0;
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
  var MAX_CYCLES = 5e3;
  var MAX_UNKNOWN = 5;
  var MAX_REOPENS = 5;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var LOG_EVERY = 25;
  var WEIGHT_BUFFER = 40;
  var PACK_LIMIT = 120;

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat(),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name].includes(matched))
  });

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
      const gump = craftGump();
      if (gump && gump.hasButton(buttonID)) {
        return gump;
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

  // src/lib/pack.ts
  var totalMatching = (matches, contents = player.backpack?.contents) => (contents ?? []).reduce(
    (total, item) => total + (matches(item) ? item.amount ?? 1 : 0) + totalMatching(matches, item.contents ?? []),
    0
  );

  // src/tinkering/ingots.ts
  var isIngot = (item) => INGOT_GRAPHICS.has(item.graphic) && (item.hue ?? 0) === INGOT_HUE;
  var ingotTotal = (contents) => totalMatching(isIngot, contents);

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
  var oplReportsUses = true;
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
  var usesRemaining = (serial) => {
    const opl = client.queryItemOPL(serial, 1e3);
    for (const property of opl?.properties ?? []) {
      const values = (property.values ?? []).map((value) => value.text).join(" ");
      const match = `${property.text ?? ""} ${values}`.match(/uses remaining[^0-9]*([0-9]+)/i);
      if (match) {
        return Number(match[1]);
      }
    }
    return void 0;
  };
  var needsSwap = (serial) => {
    if (!toolAlive(serial)) {
      return true;
    }
    if (!oplReportsUses) {
      return false;
    }
    const uses = usesRemaining(serial);
    if (uses === void 0) {
      oplReportsUses = false;
      log('tool: no "uses remaining" property, falling back to detecting the break itself');
      return false;
    }
    return uses <= 1;
  };

  // src/tinkering/craft.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var silentOutcome = (toolSerial2, ingotsBefore) => {
    if (!toolAlive(toolSerial2)) {
      return "wornOut";
    }
    const after = ingotTotal();
    if (after < ingotsBefore) {
      return "used";
    }
    if (after === 0) {
      return "noMaterial";
    }
    return "unknown";
  };
  var craftOnce = (recipe, toolSerial2) => {
    const categoryPage = openCraftGump(toolSerial2, recipe.category);
    if (!categoryPage) {
      return "noGump";
    }
    categoryPage.reply(recipe.category);
    const nextPage = NEXT_PAGE_BUTTON;
    const hops = recipe.nextPages ?? 0;
    if (hops > 0 && nextPage === void 0) {
      log("craftOnce: this recipe needs NEXT PAGE, but NEXT_PAGE_BUTTON is unset in config.ts");
      return "noGump";
    }
    for (let hop = 0; hop < hops && nextPage !== void 0; hop++) {
      const before = craftGump();
      if (!before) {
        return "noGump";
      }
      before.reply(nextPage);
      sleep(GUMP_POLL);
    }
    const itemPage = pageWith(recipe.item, GUMP_TIMEOUT);
    if (!itemPage) {
      return "noGump";
    }
    const ingotsBefore = ingotTotal();
    journal.clear();
    itemPage.reply(recipe.item);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CRAFT_TIMEOUT);
    return matched ? outcomeFor(matched) : silentOutcome(toolSerial2, ingotsBefore);
  };

  // src/lib/weight.ts
  var overweight = (buffer = 0) => player.weightMax > 0 && player.weight > player.weightMax - buffer;

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var heavy = (buffer) => () => overweight(buffer) ? `overweight (${player.weight}/${player.weightMax})` : void 0;
  var packFull = (limit) => () => {
    const top = (player.backpack?.contents ?? []).length;
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

  // src/tinkering/guards.ts
  var stopReason = () => firstReason(dead, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));

  // src/tinkering/phase.ts
  var skillBase = () => player.getSkill(Skills.Tinkering)?.base ?? 0;
  var tenths = (value) => (value / 10).toFixed(1);
  var currentPhase = () => {
    const base = skillBase();
    if (base >= STOP_AT) {
      return "done";
    }
    if (base >= RING_FROM) {
      return "rings";
    }
    return "lockpicks";
  };

  // src/tinkering/index.ts
  var uncalibrated = Object.keys(RECIPES).filter(
    (phase) => RECIPES[phase].category === void 0 || RECIPES[phase].item === void 0
  );
  var startedAt = skillBase();
  log(`tinker: base ${tenths(startedAt)}, ${ingotTotal()} iron ingots in the pack`);
  if (startedAt < LOCKPICK_FROM) {
    log(`tinker: base ${tenths(startedAt)} is under the ${tenths(LOCKPICK_FROM)} floor, making lockpicks anyway`);
  }
  var crafted = 0;
  var failures = 0;
  var unknown = 0;
  var reopens = 0;
  var throttled = 0;
  var toolSerial;
  var reported = 0;
  var stop = uncalibrated.length ? `${uncalibrated.join(" and ")} button IDs are unset - run dist/tinker-probe.js and fill in config.js` : void 0;
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    const phase = currentPhase();
    if (phase === "done") {
      stop = `base reached ${tenths(STOP_AT)}`;
      break;
    }
    if (needsSwap(toolSerial)) {
      toolSerial = findTool();
    }
    if (toolSerial === void 0) {
      stop = "out of tinker's tools";
      break;
    }
    const recipe = RECIPES[phase];
    if (!isCalibrated(recipe)) {
      stop = `${phase} has no button ID - run dist/tinker-probe.js and fill in config.ts`;
      break;
    }
    const outcome = craftOnce(recipe, toolSerial);
    switch (outcome) {
      case "success":
      case "used":
        crafted++;
        unknown = 0;
        reopens = 0;
        throttled = 0;
        break;
      case "failed":
        failures++;
        unknown = 0;
        reopens = 0;
        throttled = 0;
        break;
      case "wornOut":
        log(`tinker: tool worn out after ${crafted} ${recipe.label}s`);
        toolSerial = void 0;
        break;
      // Counted and backed off, not just slept through: a fixed retry shorter than the shard's own
      // timer re-arms the throttle it is waiting out, and the branch says nothing while it does it
      case "throttled":
        throttled++;
        log(`tinker: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
        sleep(Math.min(THROTTLE_BACKOFF * throttled, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the craft";
        }
        break;
      case "noGump":
        reopens++;
        log(`tinker: craft gump did not come back (${reopens}/${MAX_REOPENS})`);
        if (reopens >= MAX_REOPENS) {
          stop = "the craft gump stopped opening";
        }
        break;
      case "noMaterial":
        stop = "out of iron ingots";
        break;
      default:
        unknown++;
        log(`tinker: nothing observable happened (${unknown}/${MAX_UNKNOWN})`);
        if (unknown >= MAX_UNKNOWN) {
          stop = "no craft outcome could be detected - recheck OUTCOME_TEXT in config.js";
        }
    }
    if (crafted >= reported + LOG_EVERY) {
      reported = crafted;
      log(`tinker: ${crafted} made, ${failures} failed, base ${tenths(startedAt)} -> ${tenths(skillBase())}`);
    }
    sleep(STEP_DELAY);
  }
  log(`tinker: ${crafted} made, ${failures} failed, base ${tenths(startedAt)} -> ${tenths(skillBase())}, ${ingotTotal()} ingots left`);
  exit(`tinker: ${stop ?? `hit the ${MAX_CYCLES} cycle backstop`}`);
})();
