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
      const serial2 = item?.serial ?? 0;
      if (!unreadable.has(serial2)) {
        unreadable.add(serial2);
        log(`contents: ${hex(serial2)} would not answer - ${String(error)}`);
      }
      return void 0;
    }
  };
  var findIn = (contents, matches) => {
    for (const item of contents ?? []) {
      if (matches(item)) {
        return item;
      }
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        const foundInSub = findIn(sub, matches);
        if (foundInSub) return foundInSub;
      }
    }
    return null;
  };

  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/boxes/config.ts
  var PROBE_DELAY = 1200;
  var KEY_GRAPHICS = /* @__PURE__ */ new Set([4110, 4111, 4112, 4113, 4114, 4115]);

  // src/boxes/boxes.ts
  var keyGraphic;
  var KEY_WORD = /\bkey\b/i;
  var isKey = (item) => keyGraphic !== void 0 && item.graphic === keyGraphic || KEY_GRAPHICS.has(item.graphic) || KEY_WORD.test(item.name ?? "");

  // src/boxes/probe.ts
  var GROUND = 4294967295;
  var backpack = player.backpack ?? die("key-probe: no backpack");
  var resolve = (serial2) => {
    const found = client.findObject(serial2);
    return found && found._tag !== "Mobile" ? found : void 0;
  };
  var key = findIn(player.backpack?.contents, isKey);
  if (!key) {
    log("key-probe: no key in the pack. Open a box first, or add its graphic to KEY_GRAPHICS.");
    die("key-probe: nothing to test with");
  }
  var serial = key.serial;
  var graphic = key.graphic;
  var startedIn = key.container;
  log(`key-probe: testing with ${hex(serial)} (graphic ${hex(graphic)})`);
  log(`key-probe: you are at ${player.x}, ${player.y}, ${player.z}`);
  log(`key-probe: the key reports x ${key.x}, y ${key.y}, z ${key.z}, container ${hex(startedIn)}`);
  var VARIANTS = [
    {
      name: "groundOffset 0/0/0",
      note: "the documented call, at your feet",
      run: () => player.moveItemOnGroundOffset(serial, 0, 0, 0)
    },
    {
      name: "groundOffset 1/0/0",
      note: 'the same call one tile east, in case 0/0/0 reads as "do not move"',
      run: () => player.moveItemOnGroundOffset(serial, 1, 0, 0)
    },
    {
      name: "moveItem to GROUND with coordinates",
      note: "addressed the way the drop packet does it",
      run: () => player.moveItem(serial, GROUND, player.x, player.y, player.z)
    },
    {
      name: "moveItem to GROUND without coordinates",
      note: "in case the client fills the position in itself",
      run: () => player.moveItem(serial, GROUND)
    },
    {
      name: "moveItem to container 0 with coordinates",
      note: 'some clients spell "no container" as zero rather than -1',
      run: () => player.moveItem(serial, 0, player.x, player.y, player.z)
    },
    {
      name: "moveTypeOnGroundOffset from the pack",
      note: "the by-graphic twin of the first call, which names a source container",
      run: () => player.moveTypeOnGroundOffset(graphic, backpack.serial, 0, 0, 0)
    },
    {
      name: "into the pack first, then groundOffset 0/0/0",
      note: "tests whether the offset works once the item is somewhere the client tracks",
      run: () => {
        player.moveItem(serial, backpack.serial);
        sleep(PROBE_DELAY);
        player.moveItemOnGroundOffset(serial, 0, 0, 0);
      }
    },
    {
      name: "into the pack first, then groundOffset 1/0/0",
      note: "the same, one tile east",
      run: () => {
        player.moveItem(serial, backpack.serial);
        sleep(PROBE_DELAY);
        player.moveItemOnGroundOffset(serial, 1, 0, 0);
      }
    }
  ];
  var winner;
  for (const variant of VARIANTS) {
    log(`key-probe: trying ${variant.name} - ${variant.note}`);
    variant.run();
    sleep(PROBE_DELAY);
    const after = resolve(serial);
    if (!after) {
      log(`key-probe:   the key no longer resolves - it is off you. ${variant.name} WORKS.`);
      winner = variant.name;
      break;
    }
    log(
      `key-probe:   still here: container ${hex(after.container)}, x ${after.x}, y ${after.y}, z ${after.z}`
    );
    if (after.container !== startedIn && after.container !== backpack.serial) {
      log(`key-probe:   it left both the box and the pack. ${variant.name} WORKS.`);
      winner = variant.name;
      break;
    }
  }
  if (winner) {
    log(`key-probe: use '${winner}'. Tell Claude, or set DROP_METHOD in src/boxes/config.ts.`);
  } else {
    log("key-probe: nothing moved the key off you. Paste this whole log back and we will read it.");
  }
  exit(`key-probe: ${winner ?? "no variant worked"}`);
})();
