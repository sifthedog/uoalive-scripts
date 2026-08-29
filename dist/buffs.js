"use strict";
(() => {
  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var HEARTBEAT_EVERY = 3e4;
  var MAX_THROTTLED = 20;
  var THROTTLE_BACKOFF = 1e3;
  var THROTTLE_BACKOFF_MAX = 8e3;
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
  var HOSTILE_NOTORIETY = 16 | 8 | 2 | 4;
  var CALL_ON_SIGHT_NOTORIETY = 8 | 2 | 4;

  // src/buffs/config.ts
  var KEEP = [
    {
      spell: Spells.ConsecrateWeapon,
      buff: BuffDebuffs.ConsecrateWeapon,
      mana: 10,
      needsWeapon: true
    },
    { spell: Spells.DivineFury, buff: BuffDebuffs.DivineFury, mana: 15 }
  ];
  var POLL = 1e3;
  var CAST_TIMEOUT = 1e3;
  var CAST_DELAY = 600;
  var MAX_MISSES = 5;
  var SET_ASIDE = 6e4;
  var MAX_CYCLES = 1e5;
  var KEEP_UP = true;
  var OUTCOME_TEXT = {
    // Not depended on: the buff arriving and the mana leaving the pool are the proof
    cast: ["Your weapon is consecrated", "You are filled with divine fury"],
    fizzled: ["You fail to cast the spell", "The spell fizzles"],
    noTithing: [
      "You do not have enough tithing points",
      "You must have at least",
      "You need to make an offering"
    ],
    noMana: ["You do not have enough mana", "Insufficient mana"],
    alreadyUp: ["You are already under the effect"],
    noWeapon: [
      "You cannot consecrate your fists",
      "You must have a weapon",
      "You must be wielding a weapon"
    ],
    unskilled: ["You are not pious enough", "Your karma is not high enough", ...UNSKILLED_TEXT],
    saving: SAVING_TEXT,
    // Before throttled: waitForTextAny hands back whichever string it found, and THROTTLED_TEXT ends
    // in a bare 'You must wait' that a longer sentence can contain.
    alreadyCasting: ["You are already casting a spell", "You are already casting"],
    throttled: THROTTLED_TEXT
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

  // src/buffs/guards.ts
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

  // src/buffs/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "buffs",
    noun: "casts",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/lib/cast.ts
  var buffUp = (cast) => cast.buff !== void 0 && player.hasBuffDebuff(cast.buff);
  var issue = (cast) => {
    if (cast.target === "self") {
      player.castTo(cast.spell, player);
      return;
    }
    player.cast(cast.spell);
  };
  var createCaster = ({ outcomeText, timeoutMs, skipWhenBuffed }) => {
    const { all, outcomeFor: outcomeFor2 } = outcomeVocabulary(outcomeText);
    const silentOutcome = (cast, upBefore, manaBefore) => {
      if (!upBefore && buffUp(cast)) {
        return "cast";
      }
      if (player.mana < manaBefore) {
        return "cast";
      }
      return void 0;
    };
    return {
      allText: all,
      outcomeFor: outcomeFor2,
      // outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given -
      // but the caller's switch has a default for it, so the maybe is kept rather than asserted away.
      castOnce: (cast) => {
        const upBefore = buffUp(cast);
        if (skipWhenBuffed && upBefore) {
          return "alreadyUp";
        }
        const manaBefore = player.mana;
        target.cancel();
        journal.clear();
        issue(cast);
        const matched = journal.waitForTextAny(all, void 0, cast.castTimeout ?? timeoutMs);
        if (matched) {
          return outcomeFor2(matched);
        }
        return silentOutcome(cast, upBefore, manaBefore);
      }
    };
  };

  // src/lib/stages.ts
  var spellName = (spell) => Spells[spell] ?? `spell ${spell}`;

  // src/buffs/keep.ts
  var { allText, castOnce, outcomeFor } = /* @__PURE__ */ createCaster({
    outcomeText: OUTCOME_TEXT,
    timeoutMs: CAST_TIMEOUT,
    skipWhenBuffed: true
  });
  var roster = () => KEEP.map((entry) => ({ entry, name: spellName(entry.spell), misses: 0, until: 0 }));
  var standing = (entry) => player.hasBuffDebuff(entry.buff);
  var armed = () => (player.equippedItems.twoHanded ?? player.equippedItems.oneHanded) !== void 0;
  var due = (item) => item.retired === void 0 && now() >= item.until;
  var setAside = (item, forMs) => {
    item.misses = 0;
    item.until = now() + forMs;
  };
  var retire = (item, why) => {
    item.retired = why;
  };
  var spent = (roster2) => roster2.every((item) => item.retired !== void 0);
  var settled = (roster2) => roster2.every((item) => item.retired !== void 0 || standing(item.entry));

  // src/lib/save.ts
  var createSaveWatch = (options) => ({
    isSaving: () => options.savingText.some((text) => journal.containsText(text)),
    waitOutSave: () => {
      log("save: the world is saving, waiting it out");
      const said = (texts) => texts.some((text) => journal.containsText(text));
      let ended = said(options.doneText) ? "the shard had already finished" : void 0;
      journal.clear();
      for (let waited = 0; !ended && waited < options.waitMs; waited += options.pollMs) {
        sleep(options.pollMs);
        if (said(options.doneText)) {
          ended = "the shard says it is done";
        } else if (options.stopReason()) {
          ended = "the run has a reason to stop";
        }
      }
      log(`save: ${ended ?? `nothing said in ${Math.round(options.waitMs / 1e3)}s`}, carrying on`);
      options.onDone();
    }
  });

  // src/buffs/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    onDone: resetBeat
  });

  // src/buffs/index.ts
  var PREFIX = "buffs";
  var table = roster();
  var casts = 0;
  var reported = 0;
  var throttled = 0;
  var stop;
  var saidUnarmed = false;
  var saidShort = false;
  var proved = /* @__PURE__ */ new Set();
  var sayFirst = (item) => {
    if (proved.has(item.name)) {
      return;
    }
    proved.add(item.name);
    log(`${PREFIX}: ${item.name} up`);
  };
  var backOff = () => {
    throttled++;
    if (throttled >= MAX_THROTTLED) {
      stop = `the shard refused ${MAX_THROTTLED} casts in a row`;
      return;
    }
    sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));
  };
  var landed = (item) => {
    casts++;
    throttled = 0;
    item.misses = 0;
    sayFirst(item);
  };
  var putUp = (item) => {
    const outcome = castOnce(item.entry);
    switch (outcome) {
      case "cast":
        landed(item);
        break;
      // The shard answered, so the table is right and the roll simply lost. Next pass tries again.
      case "fizzled":
      case "alreadyUp":
        throttled = 0;
        item.misses = 0;
        break;
      // The gate above cleared, so this entry's mana figure is understated for this shard
      case "noMana":
        item.misses = 0;
        log(`${PREFIX}: ${item.name} costs more than ${item.entry.mana} mana here - raise it in KEEP`);
        break;
      // Nothing a script does refills tithing points, so this entry is finished for the run
      case "noTithing":
        retire(item, "out of tithing points - tithe gold at a shrine");
        break;
      case "unskilled":
        retire(item, "the shard refuses it at this skill or karma");
        break;
      // The hand check above missed it, so believe the shard rather than the client's layers
      case "noWeapon":
        setAside(item, SET_ASIDE);
        break;
      case "saving":
        waitOutSave();
        break;
      case "cooldown":
      case "throttled":
      case "alreadyCasting":
        backOff();
        break;
      // Nothing said, no buff, and no mana left the pool: whatever this was, it did not happen
      default:
        item.misses++;
        if (item.misses >= MAX_MISSES) {
          setAside(item, SET_ASIDE);
          log(`${PREFIX}: ${item.name} did nothing ${MAX_MISSES} times - set aside; check OUTCOME_TEXT`);
        }
    }
  };
  var pass = () => {
    const hands = armed();
    if (hands) {
      saidUnarmed = false;
    }
    for (const item of table) {
      if (stop || !due(item)) {
        continue;
      }
      if (standing(item.entry)) {
        item.misses = 0;
        continue;
      }
      if (item.entry.needsWeapon && !hands) {
        if (!saidUnarmed) {
          saidUnarmed = true;
          log(`${PREFIX}: nothing in hand - ${item.name} is waiting for you to draw something`);
        }
        continue;
      }
      if (player.mana < item.entry.mana) {
        if (!saidShort) {
          saidShort = true;
          log(`${PREFIX}: ${player.mana}/${item.entry.mana} mana for ${item.name} - waiting for it`);
        }
        continue;
      }
      saidShort = false;
      putUp(item);
      sleep(CAST_DELAY);
    }
  };
  log(`${PREFIX}: keeping ${table.map((item) => item.name).join(" and ")} up`);
  if (!armed() && table.some((item) => item.entry.needsWeapon)) {
    log(`${PREFIX}: nothing in hand - the weapon enchants will be refused until you draw something`);
  }
  log(`${PREFIX}: every cast spends tithing points; tithe gold at a shrine before a long run`);
  for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
    stop = stopReason();
    if (stop) {
      break;
    }
    if (isSaving()) {
      waitOutSave();
      continue;
    }
    pass();
    if (stop) {
      break;
    }
    if (spent(table)) {
      stop = "every buff was refused for good";
      break;
    }
    if (!KEEP_UP && settled(table)) {
      stop = "everything that could go up is up";
      break;
    }
    if (casts >= reported + LOG_EVERY) {
      reported = casts;
      log(`${PREFIX}: ${casts} casts, ${player.mana}/${player.maxMana} mana`);
    }
    beat("watching the buff bar", cycle, casts);
    sleep(POLL);
  }
  for (const item of table) {
    if (item.retired) {
      log(`${PREFIX}: ${item.name} was set aside - ${item.retired}`);
    }
  }
  var reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
  log(`${PREFIX}: ${casts} casts, stopping - ${reason}`);
  exit(`${PREFIX}: ${reason}`);
})();
