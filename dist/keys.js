"use strict";
(() => {
  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;

  // src/lib/containers.ts
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
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/boxes/config.ts
  var DROP_SPREAD = [
    { x: 0, y: 0, z: 0 },
    { x: 1, y: 0, z: 0 },
    { x: 0, y: 1, z: 0 },
    { x: 1, y: 1, z: 0 },
    { x: -1, y: 0, z: 0 },
    { x: 0, y: -1, z: 0 },
    { x: -1, y: -1, z: 0 },
    { x: 1, y: -1, z: 0 },
    { x: -1, y: 1, z: 0 }
  ];
  var LOG_EVERY_KEY = 5;
  var MAX_STUCK = 3;
  var DROP_METHOD = "groundOffset";
  var DROP_TIMEOUT = 3e3;
  var DROP_POLL = 200;
  var KEY_GRAPHICS = /* @__PURE__ */ new Set([4110, 4111, 4112, 4113, 4114, 4115]);

  // src/boxes/drop.ts
  var spread = 0;
  var nextTile = () => DROP_SPREAD[spread++ % DROP_SPREAD.length] ?? { x: 0, y: 0, z: 0 };
  var GROUND = 4294967295;
  var ATTEMPTS = {
    // The documented call. The offset is from the character, which dist/key-probe.js proved.
    groundOffset: (item, tile) => player.moveItemOnGroundOffset(item.serial, tile.x, tile.y, tile.z),
    // The same call one tile east, in case an offset of 0/0/0 reads as "do not move"
    groundOffsetStep: (item) => player.moveItemOnGroundOffset(item.serial, 1, 0, 0),
    // A drop addressed the way the protocol does it: the ground's own container serial, and the
    // world coordinates to land on
    worldSerial: (item, tile) => player.moveItem(item.serial, GROUND, player.x + tile.x, player.y + tile.y, player.z + tile.z)
  };
  var ORDER = ["groundOffset", "groundOffsetStep", "worldSerial"];
  var proven = DROP_METHOD === "auto" ? void 0 : DROP_METHOD;
  var exhausted = false;
  var containerOf = (serial) => {
    const found = client.findObject(serial);
    return found && found._tag !== "Mobile" ? found.container : void 0;
  };
  var left = (serial, from) => {
    for (let waited = 0; waited < DROP_TIMEOUT; waited += DROP_POLL) {
      sleep(DROP_POLL);
      if (containerOf(serial) !== from) {
        return true;
      }
    }
    return false;
  };
  var dropToGround = (item, from) => {
    if (exhausted) {
      return false;
    }
    const tile = nextTile();
    if (proven) {
      ATTEMPTS[proven](item, tile);
      return left(item.serial, from);
    }
    for (const candidate of ORDER) {
      ATTEMPTS[candidate](item, tile);
      if (left(item.serial, from)) {
        proven = candidate;
        log(`boxes: dropping works via '${candidate}' - pin it as DROP_METHOD to skip the retries`);
        return true;
      }
    }
    exhausted = true;
    log(
      `boxes: none of ${ORDER.join(", ")} would put a key on the floor. Keys are going into the pack instead - set DROP_KEYS = false to stop trying, and say so if you want another way in.`
    );
    return false;
  };

  // src/boxes/boxes.ts
  var keyGraphic;
  var KEY_WORD = /\bkey\b/i;
  var isKey = (item) => keyGraphic !== void 0 && item.graphic === keyGraphic || KEY_GRAPHICS.has(item.graphic) || KEY_WORD.test(item.name ?? "");
  var dumpPack = () => {
    log("boxes: pack contents (graphic / hue / amount / name)");
    for (const item of player.backpack?.contents ?? []) {
      log(
        `boxes:   ${hex(item.graphic)} hue ${item.hue ?? 0} x${item.amount ?? 1} "${item.name ?? ""}"`
      );
    }
  };

  // src/boxes/keys.ts
  var backpack = player.backpack ?? die("keys: no backpack");
  var keys = collectIn(player.backpack?.contents, isKey);
  if (keys.length === 0) {
    log("keys: nothing in the pack looks like a key.");
    dumpPack();
    die("keys: nothing to drop - put the right graphic in KEY_GRAPHICS in config.ts");
  }
  log(`keys: ${keys.length} keys in the pack, dropping them at your feet`);
  var dropped = 0;
  var running = 0;
  var stuck = [];
  var stop;
  for (const [index, key] of keys.entries()) {
    if (player.isDead) {
      stop = "you are dead";
      break;
    }
    if (dropToGround(key, key.container || backpack.serial)) {
      dropped++;
      running = 0;
    } else {
      stuck.push(key);
      running++;
    }
    if (running >= MAX_STUCK) {
      stop = `${running} keys in a row would not drop`;
      break;
    }
    if ((index + 1) % LOG_EVERY_KEY === 0) {
      log(`keys: ${dropped} down, ${keys.length - index - 1} to go`);
    }
  }
  if (stuck.length) {
    log(`keys: ${stuck.length} would not go: ${stuck.map((key) => hex(key.serial)).join(", ")}`);
  }
  log(`keys: ${dropped} of ${keys.length} on the floor`);
  exit(`keys: ${stop ?? `dropped ${dropped}`}`);
})();
