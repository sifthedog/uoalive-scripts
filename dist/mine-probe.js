"use strict";
(() => {
  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill"
  ];

  // src/mining/config.ts
  var range = (from, to) => Array.from({ length: to - from + 1 }, (_, offset) => from + offset);
  var ORE_TILE_GRAPHICS = /* @__PURE__ */ new Set([
    ...range(220, 251),
    ...range(1339, 1359),
    ...range(1361, 1383),
    ...range(1386, 1394)
  ]);
  var NOT_ORE_GRAPHICS = /* @__PURE__ */ new Set();
  var ORE_STATIC_NAME = /cave|rock|mountain|ore/i;
  var RESPAWN_DELAY = 25 * 60 * 1e3;
  var UNSKILLED_TEXT2 = [
    "You have no idea how to smelt this strange ore",
    ...UNSKILLED_TEXT
  ];
  var PROBE_RADIUS = 16;

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/tiles.ts
  var tileKey = (tile) => `${tile.x},${tile.y},${tile.z},${tile.graphic}`;
  var minutes = (ms) => Math.max(1, Math.round(ms / 6e4));
  var createTileStore = (options) => {
    const block = (tile, until) => options.blocked().set(tileKey(tile), until);
    return {
      block,
      markDepleted: (tile) => {
        block(tile, now() + options.depletedFor);
        log(
          `${options.label}: ${tile.x},${tile.y} ${options.depleted}, back in ${minutes(options.depletedFor)}m`
        );
      },
      markUnreachable: (tile) => {
        block(tile, now() + options.unreachableFor);
        log(
          `${options.label}: ${tile.x},${tile.y} could not be walked to, retrying in ${minutes(options.unreachableFor)}m`
        );
      },
      markUnusable: (tile, reason) => {
        block(tile, Infinity);
        log(`${options.label}: ${tile.x},${tile.y} ${reason}, ignoring it from here on`);
      }
    };
  };

  // src/lib/store.ts
  var scope = globalThis;
  var createStore = (options) => {
    let held;
    const load = () => {
      const found2 = scope[options.key];
      if (found2?.version === options.version) {
        const described = options.describe?.(found2);
        if (described) {
          log(described);
        }
        return found2;
      }
      const fresh = { ...options.seed(), version: options.version };
      scope[options.key] = fresh;
      return fresh;
    };
    return {
      // Read through a call rather than handed out as the object itself, so forget() can actually
      // forget: a module-scope `const memory = load()` would give every importer a reference that
      // outlives it.
      read: () => held ?? (held = load()),
      // Tests only. The suite's vi.resetModules() gives each test a fresh module registry but leaves
      // globalThis alone, which is precisely what this store is designed to survive.
      forget: () => {
        delete scope[options.key];
        held = void 0;
      }
    };
  };

  // src/mining/memory.ts
  var KEY = "__mining_memory";
  var VERSION = 1;
  var store = /* @__PURE__ */ createStore({
    key: KEY,
    version: VERSION,
    seed: () => ({ blocked: /* @__PURE__ */ new Map(), notOre: /* @__PURE__ */ new Set() }),
    describe: (found2) => found2.blocked.size > 0 || found2.notOre.size > 0 ? `memory: resuming with ${found2.blocked.size} blocked tiles, ${found2.notOre.size} arts` : void 0
  });
  var memory = store.read;
  var forget = store.forget;

  // src/mining/vein.ts
  var known = /* @__PURE__ */ new Map();
  var artKey = (graphic, isLand) => `${isLand ? "land" : "static"}:${graphic}`;
  var isOre = (graphic, isLand) => {
    if (NOT_ORE_GRAPHICS.has(graphic) || memory().notOre.has(artKey(graphic, isLand))) {
      return false;
    }
    if (isLand) {
      return ORE_TILE_GRAPHICS.has(graphic);
    }
    const remembered = known.get(graphic);
    if (remembered !== void 0) {
      return remembered;
    }
    const name = client.getStatic(graphic)?.name ?? "";
    const matches = ORE_STATIC_NAME.test(name);
    known.set(graphic, matches);
    return matches;
  };
  var store2 = /* @__PURE__ */ createTileStore({
    label: "vein",
    blocked: () => memory().blocked,
    depletedFor: RESPAWN_DELAY,
    unreachableFor: UNREACHABLE_DELAY,
    depleted: "is out of ore"
  });
  var markDepleted = store2.markDepleted;
  var markUnreachable = store2.markUnreachable;
  var markUnusable = store2.markUnusable;

  // src/mining/survey.ts
  var surveyTerrain = (radius) => {
    const seen = /* @__PURE__ */ new Map();
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        for (const tile of client.getTerrainList(player.x + dx, player.y + dy) ?? []) {
          const key = `${tile.graphic}/${tile.isLand}`;
          const already = seen.get(key);
          if (already) {
            already.tiles++;
            continue;
          }
          seen.set(key, {
            graphic: tile.graphic,
            isLand: tile.isLand,
            flags: tile.flags,
            tiles: 1,
            name: tile.isLand ? "" : client.getStatic(tile.graphic)?.name ?? "?",
            matches: isOre(tile.graphic, tile.isLand)
          });
        }
      }
    }
    return [...seen.values()].sort((a, b) => b.tiles - a.tiles);
  };
  var describeArt = (art) => {
    const kind = art.isLand ? "land" : `static '${art.name}'`;
    const mark = art.matches ? "MATCHES" : "-";
    return `${art.graphic} (0x${art.graphic.toString(16)}) ${kind}, flags 0x${art.flags.toString(16)}, ${art.tiles} tiles, ${mark}`;
  };
  var reportTerrain = (radius, limit = Infinity) => {
    const found2 = surveyTerrain(radius);
    log(`survey: ${found2.length} distinct arts within ${radius} tiles of ${player.x},${player.y}`);
    for (const art of found2.slice(0, limit)) {
      log(`survey: ${describeArt(art)}`);
    }
    if (found2.length > limit) {
      log(`survey: ${found2.length - limit} rarer arts not shown, run dist/mine-probe.js for all`);
    }
    return found2;
  };

  // src/mining/probe.ts
  log(`probe: ORE_TILE_GRAPHICS currently holds ${ORE_TILE_GRAPHICS.size} graphics`);
  var found = reportTerrain(PROBE_RADIUS);
  var matched = found.filter((art) => art.matches);
  if (matched.length === 0) {
    log("probe: nothing here matches. The land graphics above are the candidates to add.");
  } else {
    const tiles = matched.reduce((total, art) => total + art.tiles, 0);
    log(`probe: ${matched.length} art(s) match, covering ${tiles} tiles`);
  }
  log("probe: put the land graphics you mean to mine into ORE_TILE_GRAPHICS, then run dist/mining.js");
})();
