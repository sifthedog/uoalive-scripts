"use strict";
(() => {
  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var SAVING_TEXT = ["The world is saving", "Saving world", "World save started"];
  var THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait"
  ];
  var UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill"
  ];

  // src/magery/config.ts
  var SKILL = Skills.Magery;
  var STAGES = [
    // 3rd circle. Below about 30 the sensible thing is to buy the skill from an NPC trainer.
    {
      upTo: 450,
      spell: Spells.Bless,
      mana: 9,
      buff: BuffDebuffs.Bless,
      target: "self",
      castTimeout: 1200,
      castDelay: 300
    },
    // 4th circle
    {
      upTo: 600,
      spell: Spells.ArchProtection,
      mana: 11,
      buff: BuffDebuffs.ArchProtection,
      target: "self",
      castTimeout: 1500,
      castDelay: 350
    },
    // 6th. The 5th and 7th circles are skipped because their spells want a cursor over ground or a
    // gump answered, and neither is something this loop can do.
    {
      upTo: 800,
      spell: Spells.Invisibility,
      mana: 20,
      buff: BuffDebuffs.Invisibility,
      target: "self",
      castTimeout: 2500,
      castDelay: 400
    },
    // 8th. An area attack that hits everything nearby, so this band belongs somewhere empty. The
    // longest timeout of the four and the only row that needs it: no buff, so the mana falling is the
    // whole proof, and a window that closes first turns every cast here into an unread outcome.
    { upTo: 1200, spell: Spells.Earthquake, mana: 50, castTimeout: 3200, castDelay: 600 }
  ];
  var STRIP_LAYERS = [
    Layers.OneHanded,
    Layers.TwoHanded,
    Layers.Helmet,
    Layers.Gloves,
    Layers.Arms,
    Layers.Torso,
    Layers.Tunic,
    Layers.Legs,
    Layers.Pants,
    Layers.Shirt,
    Layers.Waist,
    Layers.Skirt,
    Layers.Robe,
    Layers.Cloak,
    Layers.Shoes
  ];
  var MEDITATE_OUTCOME_TEXT = {
    trance: ["You enter a meditative trance."],
    full: ["You are at peace"],
    // Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
    // concentration' would also match the equipped-weapon sentence.
    blocked: [
      "You cannot focus your concentration with an equipped weapon",
      "You cannot focus your concentration with an equipped shield",
      "You are preoccupied with thoughts of battle"
    ],
    unfocused: ["You cannot focus your concentration.", "You lose your concentration"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: ["You must wait a few moments to use another skill", ...THROTTLED_TEXT]
  };

  // src/magery/probe.ts
  log("probe: --- 1. what the client says is on the character ---");
  var named = Object.entries(Layers).filter(
    (entry) => typeof entry[1] === "number"
  );
  var seen = [];
  for (const [name, layer] of named) {
    const item = client.findItemOnLayer(player.serial, layer);
    if (item) {
      seen.push(`${name}=${(item.graphic >>> 0).toString(16)} '${item.name ?? ""}'`);
    }
  }
  var worn = Object.entries(player.equippedItems).filter(([, item]) => item !== void 0);
  log(`probe: findItemOnLayer sees ${seen.length} piece(s): ${seen.join(", ") || "NOTHING"}`);
  log(`probe: equippedItems sees ${worn.length} piece(s): ${worn.map(([key]) => key).join(", ")}`);
  if (seen.length === 0 && worn.length > 0) {
    log("probe: >>> findItemOnLayer answers nothing for the player on this shard.");
    log("probe: >>> That is the fault. Nothing will ever be stripped until it is worked around.");
  } else if (seen.length < worn.length) {
    log("probe: >>> the two views disagree - the layers missing above will never be stripped");
  }
  var strippable = STRIP_LAYERS.filter(
    (layer) => client.findItemOnLayer(player.serial, layer) !== void 0
  ).length;
  log(`probe: ${strippable} of those sit on a layer STRIP_LAYERS actually lists`);
  if (strippable < seen.length) {
    log("probe: the rest are on layers STRIP_LAYERS leaves out - jewellery and Necklace, by default");
  }
  if (player.backpack === void 0) {
    log("probe: >>> the client reports no backpack, so no strip can ever land");
  }
  log("probe: --- 2. what the shard says when it refuses a trance ---");
  if (player.mana >= player.maxMana && player.maxMana > 0) {
    log('probe: the pool is full, so the answer will be "at peace" and will tell us nothing.');
    log("probe: spend some mana and run this again.");
  } else {
    const CANDIDATES = [
      "You enter a meditative trance",
      "You are at peace",
      "You cannot focus your concentration with an equipped weapon",
      "You cannot focus your concentration with an equipped shield",
      "You cannot meditate with a weapon equipped",
      "You cannot meditate while holding",
      "You are preoccupied with thoughts of battle",
      "You cannot focus your concentration",
      "You lose your concentration",
      "Regenerative forces cannot penetrate your armor",
      "Your armor is too heavy",
      "You must wait",
      "You are not skilled enough"
    ];
    journal.clear();
    player.useSkill(Skills.Meditation);
    const matched = journal.waitForTextAny(CANDIDATES, void 0, 3e3);
    if (matched) {
      log(`probe: the shard said "${matched}"`);
    } else {
      log("probe: the shard said none of the wordings this probe knows.");
      log("probe: read the journal by eye and copy the exact line into MEDITATE_OUTCOME_TEXT.blocked.");
    }
    const buff = player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, 2e3);
    log(`probe: ActiveMeditation buff answered ${buff === null ? "nothing" : String(buff)}`);
    if (buff === true) {
      log("probe: the trance STARTED while dressed - armour is not what is blocking you here.");
      log("probe: if mana still crawls, this shard slows regeneration rather than refusing the trance,");
      log("probe: and STRIP_AT_ONCE = true is the setting that answers it.");
    }
  }
  log("probe: --- what to do with this ---");
  log("probe: armour only comes off after a refusal whose wording is in MEDITATE_OUTCOME_TEXT.blocked.");
  log("probe: if section 2 shows no such refusal, set STRIP_AT_ONCE = true in config.ts instead.");
})();
