"use strict";
(() => {
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
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var PROBE_RADIUS = 16;

  // src/mining/memory.ts
  var KEY = "__mining_memory";
  var VERSION = 1;
  var scope = globalThis;
  var load = () => {
    const found2 = scope[KEY];
    if (found2?.version === VERSION) {
      if (found2.blocked.size > 0 || found2.notOre.size > 0) {
        log(`memory: resuming with ${found2.blocked.size} blocked tiles, ${found2.notOre.size} arts`);
      }
      return found2;
    }
    const store2 = { version: VERSION, blocked: /* @__PURE__ */ new Map(), notOre: /* @__PURE__ */ new Set() };
    scope[KEY] = store2;
    return store2;
  };
  var store;
  var memory = () => store ?? (store = load());

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
