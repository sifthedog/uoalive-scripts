"use strict";
(() => {
  // src/lib/die.ts
  var die = (reason2) => {
    exit(reason2);
    throw new Error(reason2);
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var describeItem = (item) => item ? `${hex(item.graphic)} '${item.name ?? ""}'` : "empty";

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap2) => Math.min(step * count, cap2);

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat(),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name].includes(matched))
  });

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var STEP_DELAY = 300;
  var EQUIP_TIMEOUT = 2e3;
  var EQUIP_POLL = 200;
  var EQUIP_ATTEMPTS = 3;
  var MAX_CYCLES = 5e3;
  var HEARTBEAT_EVERY = 3e4;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
  var MAX_UNKNOWN = 5;
  var LOG_EVERY = 25;
  var SAVE_WAIT = 6e4;
  var SAVE_POLL = 1e3;
  var SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"];
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

  // src/training/config.ts
  var SKILL = Skills.Bushido;
  var SKILL_LABEL = "Bushido";
  var STAGES = [
    { upTo: 600, spell: Spells.Confidence, mana: 10, buff: BuffDebuffs.Confidence },
    { upTo: 750, spell: Spells.CounterAttack, mana: 5, buff: BuffDebuffs.CounterAttack },
    { upTo: 1050, spell: Spells.Evasion, mana: 10, buff: BuffDebuffs.Evasion }
  ];
  var WEAPON_NAME = "double axe";
  var SPARE_BAG_SERIAL = void 0;
  var DISARM_TIMEOUT = 2e3;
  var DISARM_POLL = 200;
  var DISARM_ATTEMPTS = 3;
  var SKILL_TIMEOUT = 1e3;
  var SKILL_POLL = 500;
  var MAX_BLIND_READS = 5;
  var CAST_TIMEOUT = 500;
  var CAST_DELAY = 500;
  var SKIP_WHEN_BUFFED = false;
  var BUFF_WAIT = 2e3;
  var COOLDOWN_BACKOFF = 2e3;
  var COOLDOWN_BACKOFF_MAX = 2e4;
  var MEDITATE = true;
  var MEDITATE_TO_FULL = true;
  var MEDITATE_TIMEOUT = 2e4;
  var MEDITATE_ATTEMPTS = 4;
  var MEDITATE_START_TIMEOUT = 2e3;
  var MANA_POLL = 500;
  var MANA_LOG_EVERY = 1e4;
  var REGEN_TIMEOUT = 12e4;
  var MAX_HUNGRY = 5;
  var OUTCOME_TEXT = {
    // The one bucket the run does not depend on. A cast is proved by the mana leaving the pool and the
    // buff arriving, both of which are wording-free - see castOnce's silentOutcome. This is here so a
    // shard that does say something is read at once rather than waited out.
    cast: ["You have enabled", "You are infused with", "You gain confidence"],
    // A failed casting roll, and the commonest outcome there is at a low skill - confirmed in play,
    // where it ended a run at five in a row before it had a bucket. Ordinary rather than a fault: the
    // shard charged nothing for it, which is why it reads as silence to silentOutcome and has to be
    // read from the words instead.
    fizzled: ["The spell fizzles"],
    // Belt and braces: the loop gathers mana before it casts, so reaching this means lowerManaCost, a
    // stale read, or a mana figure in the stage row that is too low. The branch says which.
    noMana: [
      "You do not have enough mana to perform that attack",
      "You lack sufficient mana",
      "Insufficient mana"
    ],
    // Reaching this at all means the buff gate did not see the ability standing, which is worth knowing:
    // on this family of shards the next cast toggles it back off.
    alreadyUp: ["You are already under the effect"],
    disabled: ["You have disabled"],
    // These are weapon abilities on most shards, and an empty hand is what a draw that did not land
    // leaves behind - which is why the loop answers this by drawing again rather than by stopping.
    noWeapon: ["You must have a weapon", "You cannot perform this ability"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    // The ability's own cooldown, and it must come before throttled: waitForTextAny hands back whichever
    // of the strings it was given it found, and THROTTLED_TEXT ends in a bare 'You must wait' that this
    // sentence contains. Listed first, it is the one that comes back - the same full-wording-before-
    // prefix ordering timings.ts uses inside THROTTLED_TEXT itself.
    //
    // Telling the two apart is not pedantry. A throttle is a fault worth giving up over after
    // MAX_THROTTLED of them; a cooldown is the ability working as designed, and Evasion spends most of
    // its time in one. Bucketed together, the Evasion stage ends every run it reaches.
    cooldown: ["You must wait before trying again"],
    throttled: THROTTLED_TEXT
  };
  var MEDITATE_OUTCOME_TEXT = {
    trance: ["You enter a meditative trance."],
    full: ["You are at peace"],
    // The run stows the weapon before it meditates, so reaching this means something else is refusing
    // the trance - a shield, an off-hand item, or a shard that gates meditation another way. Nothing
    // retried fixes any of those, so it latches meditation off and falls back on natural regeneration.
    blocked: [
      "You cannot focus your concentration with an equipped weapon",
      "You cannot focus your concentration with an equipped shield",
      "You are preoccupied with thoughts of battle"
    ],
    // A failed concentration roll or a trance broken by a hit. Both are fixed by using the skill again
    // in a moment, which is exactly what the bucket above is not.
    unfocused: ["You cannot focus your concentration.", "You lose your concentration"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: ["You must wait a few moments to use another skill", ...THROTTLED_TEXT]
  };

  // src/training/cast.ts
  var { all: ALL_OUTCOME_TEXT, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);
  var buffUp = (stage) => stage.buff !== void 0 && player.hasBuffDebuff(stage.buff);
  var silentOutcome = (stage, upBefore, manaBefore) => {
    if (!upBefore && buffUp(stage)) {
      return "cast";
    }
    if (player.mana < manaBefore) {
      return "cast";
    }
    return void 0;
  };
  var castOnce = (stage) => {
    const upBefore = buffUp(stage);
    if (SKIP_WHEN_BUFFED && upBefore) {
      return "alreadyUp";
    }
    const manaBefore = player.mana;
    journal.clear();
    player.cast(stage.spell);
    const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, void 0, CAST_TIMEOUT);
    if (matched) {
      return outcomeFor(matched);
    }
    return silentOutcome(stage, upBefore, manaBefore);
  };

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
  var openContainers = (preferredSerial) => {
    if (preferredSerial) {
      player.use(preferredSerial);
      sleep(800);
      return true;
    }
    let opened = false;
    for (const item of packContents() ?? []) {
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
      const sub = contentsOf(item);
      if (sub && sub.length > 0) {
        const foundInSub = findIn(sub, matches);
        if (foundInSub) return foundInSub;
      }
    }
    return null;
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

  // src/training/guards.ts
  var stopReason = () => firstReason(dead);

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

  // src/training/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "train",
    noun: "casts",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/vitals.ts
  var manaCeiling = () => player.maxMana > 0 ? player.maxMana : void 0;

  // src/lib/save.ts
  var createSaveWatch = (options) => ({
    isSaving: () => options.savingText.some((text) => journal.containsText(text)),
    waitOutSave: () => {
      log("save: the world is saving, waiting it out");
      journal.clear();
      for (let waited = 0; waited < options.waitMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (options.doneText.some((text) => journal.containsText(text))) {
          break;
        }
        if (options.stopReason()) {
          break;
        }
      }
      options.onDone();
    }
  });

  // src/training/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/lib/retry.ts
  var untilLanded = (options) => {
    for (let attempt = 1; attempt <= options.attempts; attempt++) {
      options.act();
      for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (options.landed()) {
          return true;
        }
      }
      log(`${options.label}: attempt ${attempt} did not land, reissuing`);
    }
    log(`${options.label}: gave up`);
    return false;
  };

  // src/lib/tool.ts
  var describeContents = (contents) => (contents ?? []).map((item) => {
    const sub = contentsOf(item);
    return sub?.length ? `${hex(item.graphic)}[${describeContents(sub)}]` : hex(item.graphic);
  }).join(", ");
  var createTool = (options) => {
    let learned;
    let spareBagSerial = options.spareBagSerial;
    let reportedEmpty = false;
    const is = (item) => learned !== void 0 && item.graphic === learned || (options.graphics?.has(item.graphic) ?? false) || (item.name ?? "").toLowerCase().includes(options.name);
    const remember = (item) => {
      if (item && learned === void 0) {
        learned = item.graphic;
        log(`${options.label}: graphic is ${hex(item.graphic)}`);
      }
    };
    const reportEmptyPack = () => {
      if (reportedEmpty) {
        return;
      }
      log(`${options.label}: none found. Pack holds: ${describeContents(packContents())}`);
      log(`${options.label}: if the spares are in a bag inside a bag, pin it as SPARE_BAG_SERIAL`);
      reportedEmpty = true;
    };
    const find = () => {
      let found = findIn(packContents(), is);
      if (!found && openContainers(spareBagSerial)) {
        found = findIn(packContents(), is);
      }
      if (!found) {
        reportEmptyPack();
        return void 0;
      }
      reportedEmpty = false;
      remember(found);
      if (found.container && found.container !== player.backpack?.serial) {
        spareBagSerial = found.container;
      }
      return found;
    };
    const stillHolding = () => {
      const item = options.held();
      return !!item && is(item) && client.findObject(item.serial) !== void 0;
    };
    return {
      is,
      remember,
      find,
      serial: () => options.held()?.serial,
      equip: () => {
        if (stillHolding()) {
          return true;
        }
        const found = find();
        if (!found) {
          client.headMsg(`No ${options.name}!`, player, 33);
          return false;
        }
        target.cancel();
        return untilLanded({
          label: `equip ${options.name}`,
          attempts: options.equip.attempts,
          timeoutMs: options.equip.timeoutMs,
          pollMs: options.equip.pollMs,
          act: () => player.equip(found.serial),
          landed: () => options.held()?.serial === found.serial
        });
      }
    };
  };

  // src/training/weapon.ts
  var weapon = /* @__PURE__ */ createTool({
    label: "weapon",
    name: WEAPON_NAME,
    spareBagSerial: SPARE_BAG_SERIAL,
    // Either hand: a katana is one-handed and a no-dachi two-handed, and both train the same abilities
    held: () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL }
  });
  var held = () => player.equippedItems.twoHanded ?? player.equippedItems.oneHanded;
  var isWeapon = weapon.is;
  var rememberWeapon = weapon.remember;
  var rearm = weapon.equip;
  var disarm = () => {
    const item = held();
    if (!item) {
      return true;
    }
    rememberWeapon(item);
    const pack = player.backpack?.serial;
    if (pack === void 0) {
      log(`train: nowhere to stow ${describeItem(item)} - the client reports no backpack`);
      return false;
    }
    return untilLanded({
      label: "stow the weapon",
      attempts: DISARM_ATTEMPTS,
      timeoutMs: DISARM_TIMEOUT,
      pollMs: DISARM_POLL,
      act: () => {
        player.moveItem(item.serial, pack);
      },
      landed: () => held() === void 0
    });
  };

  // src/training/meditate.ts
  var { all: ALL_MEDITATE_TEXT, outcomeFor: meditateOutcomeFor } = outcomeVocabulary(MEDITATE_OUTCOME_TEXT);
  var refused;
  var disarmed;
  var weaponLost = () => disarmed;
  var manaTarget = (need) => {
    const ceiling = manaCeiling();
    if (!MEDITATE_TO_FULL || ceiling === void 0) {
      return need;
    }
    return Math.max(need, ceiling);
  };
  var enough = (need) => player.mana >= manaTarget(need);
  var meditating = () => player.hasBuffDebuff(BuffDebuffs.ActiveMeditation);
  var watchMana = (need, timeoutMs) => {
    let since = 0;
    for (let waited = 0; waited < timeoutMs; waited += MANA_POLL) {
      if (enough(need)) {
        return true;
      }
      if (stopReason()) {
        return false;
      }
      sleep(MANA_POLL);
      since += MANA_POLL;
      if (since >= MANA_LOG_EVERY) {
        since = 0;
        log(`train: ${player.mana}/${manaTarget(need)} mana${meditating() ? ", meditating" : ""}`);
      }
    }
    return enough(need);
  };
  var startOutcome = () => {
    const matched = journal.waitForTextAny(ALL_MEDITATE_TEXT, void 0, MEDITATE_START_TIMEOUT);
    if (matched) {
      return meditateOutcomeFor(matched) ?? "unknown";
    }
    return player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, MEDITATE_START_TIMEOUT) === true ? "trance" : "unknown";
  };
  var meditateFor = (need) => {
    for (let attempt = 1; attempt <= MEDITATE_ATTEMPTS; attempt++) {
      if (!meditating()) {
        journal.clear();
        player.useSkill(Skills.Meditation);
        const outcome = startOutcome();
        if (outcome === "blocked" || outcome === "unskilled") {
          refused = `the shard refuses meditation (${outcome})`;
          log(`train: ${refused} - check the off-hand; falling back on natural regeneration`);
          return watchMana(need, REGEN_TIMEOUT);
        }
        if (outcome === "full") {
          return true;
        }
        if (outcome === "saving") {
          waitOutSave();
        }
      }
      if (watchMana(need, MEDITATE_TIMEOUT)) {
        return true;
      }
      log(`train: meditation attempt ${attempt} did not fill the pool, using the skill again`);
    }
    return false;
  };
  var regainMana = (need) => {
    if (enough(need)) {
      return true;
    }
    log(`train: ${player.mana} mana, waiting for ${manaTarget(need)}`);
    const stowed = MEDITATE && !refused && disarm();
    const arrived = stowed ? meditateFor(need) : watchMana(need, REGEN_TIMEOUT);
    if (stowed && !rearm()) {
      disarmed = "could not get the weapon back in hand";
    }
    resetBeat();
    return arrived;
  };

  // src/lib/stages.ts
  var orderedStages = (stages) => [...stages].sort((left, right) => left.upTo - right.upTo);
  var finalTarget = (stages) => stages.reduce((highest, stage) => Math.max(highest, stage.upTo), 0);

  // src/training/plan.ts
  var PLAN = /* @__PURE__ */ orderedStages(STAGES);
  var TARGET = /* @__PURE__ */ finalTarget(PLAN);
  var stageNow = (value) => PLAN.find((stage) => value < stage.upTo);
  var spellName = (spell) => Spells[spell] ?? `spell ${spell}`;
  var describePlan = () => PLAN.map((stage) => `${spellName(stage.spell)} to ${(stage.upTo / 10).toFixed(1)}`).join(", ");

  // src/training/skill.ts
  var tenths = (value) => (value / 10).toFixed(1);
  var skillValue = () => player.getSkill(SKILL)?.value;
  var skillCap = () => player.getSkill(SKILL)?.cap;
  var skillName = () => player.getSkill(SKILL)?.name ?? SKILL_LABEL;
  var waitForSkill = () => {
    for (let waited = 0; waited < SKILL_TIMEOUT; waited += SKILL_POLL) {
      const value = skillValue();
      if (value !== void 0) {
        return value;
      }
      sleep(SKILL_POLL);
    }
    return skillValue();
  };

  // src/training/index.ts
  var TRAINED = "the last stage is finished";
  if (PLAN.length === 0) {
    die("train: STAGES is empty - there is nothing to train");
  }
  var start = waitForSkill() ?? die("train: the client is not reporting the skill");
  var weapon2 = held();
  rememberWeapon(weapon2);
  log(`train: ${skillName()} at ${tenths(start)}/${tenths(TARGET)} - ${describePlan()}`);
  log(`train: hand ${describeItem(weapon2)}, ${player.mana}/${player.maxMana} mana`);
  if (!weapon2) {
    log("train: nothing in hand - these are weapon abilities, so the first cast may be refused");
  }
  var cap = skillCap();
  if (cap !== void 0 && TARGET > cap) {
    log(
      `train: the last stage aims at ${tenths(TARGET)} and the shard caps ${skillName()} at ${tenths(cap)} - it will not finish without a power scroll`
    );
  }
  var casts = 0;
  var fizzled = 0;
  var unknown = 0;
  var throttled = 0;
  var cooling = 0;
  var hungry = 0;
  var blind = 0;
  var reported = 0;
  var casting;
  var stop = stageNow(start) ? void 0 : `${skillName()} is already at ${tenths(start)}`;
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    const value = skillValue();
    if (value === void 0) {
      blind++;
      if (blind >= MAX_BLIND_READS) {
        stop = "the client stopped reporting the skill";
        break;
      }
      beat("unreadable skill", cycle, casts);
      sleep(STEP_DELAY);
      continue;
    }
    blind = 0;
    const stage = stageNow(value);
    if (!stage) {
      stop = TRAINED;
      break;
    }
    if (stage !== casting) {
      casting = stage;
      log(`train: ${tenths(value)} - ${spellName(stage.spell)} until ${tenths(stage.upTo)}`);
    }
    if (player.mana < stage.mana) {
      if (regainMana(stage.mana)) {
        hungry = 0;
      } else {
        hungry++;
        log(`train: mana did not come back (${hungry}/${MAX_HUNGRY})`);
        if (hungry >= MAX_HUNGRY) {
          stop = "the mana never came back";
          break;
        }
      }
      stop = weaponLost();
      if (stop) {
        break;
      }
      beat("recovering mana", cycle, casts);
      sleep(STEP_DELAY);
      continue;
    }
    const outcome = castOnce(stage);
    switch (outcome) {
      case "cast":
        casts++;
        unknown = 0;
        throttled = 0;
        cooling = 0;
        break;
      // The ability's own timer, which is it working as designed rather than the shard refusing the
      // run. Never counted towards a stop for that reason: Evasion spends most of its life on cooldown,
      // and a run that gave up after twenty of these would never finish the band that casts it.
      case "cooldown":
        cooling++;
        unknown = 0;
        throttled = 0;
        sleep(backoffFor(cooling, COOLDOWN_BACKOFF, COOLDOWN_BACKOFF_MAX));
        break;
      // A failed casting roll, which is ordinary and gets commoner the lower the skill is. Counted
      // rather than tallied - the shard charged nothing for it and no ability went up - but it clears
      // the unknown budget, because a fizzle is an outcome that was read and not one that was missed.
      case "fizzled":
        fizzled++;
        unknown = 0;
        throttled = 0;
        cooling = 0;
        break;
      // Not a fault and not progress: the ability is standing and will drop on its own schedule
      case "alreadyUp":
        unknown = 0;
        sleep(BUFF_WAIT);
        break;
      // The toggle went the other way, which means the buff gate is not seeing this ability at all.
      // Said every time it happens, because each one is a cast paid for and thrown away.
      case "disabled":
        unknown = 0;
        log(`train: the shard toggled ${spellName(stage.spell)} off - check its buff in STAGES`);
        break;
      // The loop gathered mana before casting, so the stage's mana figure is understating what it costs
      case "noMana":
        unknown = 0;
        log(
          `train: refused for mana at ${player.mana} - raise ${spellName(stage.spell)}'s mana in STAGES`
        );
        regainMana(stage.mana);
        break;
      // Most likely a draw that silently did not land after the last trance, which is recoverable -
      // stopping outright would end a good run over one dropped item move
      case "noWeapon":
        unknown = 0;
        if (!rearm()) {
          stop = "the shard wants a weapon in hand and none could be drawn";
        }
        break;
      case "unskilled":
        stop = `the shard says this character cannot use ${spellName(stage.spell)}`;
        break;
      // Nothing was learned and nothing went wrong: the shard was writing its world file. Every counter
      // is reset, because whatever they had accumulated was measured against a server that was not
      // answering.
      case "saving":
        waitOutSave();
        unknown = 0;
        throttled = 0;
        break;
      case "throttled":
        throttled++;
        unknown = 0;
        log(`train: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
        sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
        if (throttled >= MAX_THROTTLED) {
          stop = "the shard kept refusing the cast";
        }
        break;
      default:
        unknown++;
        log(`train: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
    }
    stop = weaponLost();
    if (stop) {
      break;
    }
    if (unknown >= MAX_UNKNOWN) {
      stop = `${MAX_UNKNOWN} unreadable outcomes in a row`;
      break;
    }
    if (casts >= reported + LOG_EVERY) {
      reported = casts;
      log(
        `train: ${casts} casts, ${fizzled} fizzles, ${skillName()} at ${tenths(value)}/${tenths(TARGET)}, ${player.mana} mana`
      );
    }
    beat(outcome ?? "unknown", cycle, casts);
    sleep(CAST_DELAY);
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  var ended = skillValue();
  log(
    `train: ${casts} casts, ${fizzled} fizzles, ${skillName()} ${tenths(start)} -> ${ended === void 0 ? "unknown" : tenths(ended)}`
  );
  log(`train: stopping - ${reason}`);
  exit(`train: ${reason}`);
})();
