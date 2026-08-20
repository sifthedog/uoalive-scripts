"use strict";
(() => {
  // src/lib/outcomes.ts
  var outcomeVocabulary = (text) => ({
    all: Object.values(text).flat().filter((phrase) => phrase !== void 0),
    outcomeFor: (matched) => Object.keys(text).find((name) => text[name]?.includes(matched))
  });

  // src/lib/cast.ts
  var buffUp = (stage) => stage.buff !== void 0 && player.hasBuffDebuff(stage.buff);
  var issue = (stage) => {
    if (stage.target === "self") {
      player.castTo(stage.spell, player);
      return;
    }
    player.cast(stage.spell);
  };
  var createCaster = ({ outcomeText, timeoutMs, skipWhenBuffed }) => {
    const { all, outcomeFor } = outcomeVocabulary(outcomeText);
    const silentOutcome = (stage, upBefore, manaBefore) => {
      if (!upBefore && buffUp(stage)) {
        return "cast";
      }
      if (player.mana < manaBefore) {
        return "cast";
      }
      return void 0;
    };
    return {
      allText: all,
      outcomeFor,
      // outcomeFor cannot actually miss - waitForTextAny hands back one of the strings it was given -
      // but the caller's switch has a default for it, so the maybe is kept rather than asserted away.
      castOnce: (stage) => {
        const upBefore = buffUp(stage);
        if (skipWhenBuffed && upBefore) {
          return "alreadyUp";
        }
        const manaBefore = player.mana;
        target.cancel();
        journal.clear();
        issue(stage);
        const matched = journal.waitForTextAny(all, void 0, stage.castTimeout ?? timeoutMs);
        if (matched) {
          return outcomeFor(matched);
        }
        return silentOutcome(stage, upBefore, manaBefore);
      }
    };
  };

  // src/lib/vitals.ts
  var manaCeiling = () => player.maxMana > 0 ? player.maxMana : void 0;
  var hitsCeiling = () => player.maxHits > 0 ? player.maxHits : void 0;

  // src/lib/meditate.ts
  var createManaWait = ({
    prefix,
    outcomeText,
    meditate,
    toFull,
    timeoutMs,
    attempts,
    startTimeoutMs,
    pollMs,
    logEveryMs,
    regenTimeoutMs,
    stow: stow2,
    restore: restore2,
    stripMore: stripMore2,
    stopReason: stopReason2,
    resetBeat: resetBeat2,
    waitOutSave: waitOutSave2
  }) => {
    const { all, outcomeFor } = outcomeVocabulary(outcomeText);
    let refused;
    let unrestored;
    const manaTarget = (need) => {
      const ceiling = manaCeiling();
      if (!toFull || ceiling === void 0) {
        return need;
      }
      return Math.max(need, ceiling);
    };
    const enough = (need) => player.mana >= manaTarget(need);
    const meditating = () => player.hasBuffDebuff(BuffDebuffs.ActiveMeditation);
    const watchMana = (need, waitMs) => {
      let since = 0;
      for (let waited = 0; waited < waitMs; waited += pollMs) {
        if (enough(need)) {
          return true;
        }
        if (stopReason2()) {
          return false;
        }
        sleep(pollMs);
        since += pollMs;
        if (since >= logEveryMs) {
          since = 0;
          log(
            `${prefix}: ${player.mana}/${manaTarget(need)} mana${meditating() ? ", meditating" : ""}`
          );
        }
      }
      return enough(need);
    };
    const startOutcome = () => {
      const matched = journal.waitForTextAny(all, void 0, startTimeoutMs);
      if (matched) {
        return outcomeFor(matched) ?? "unknown";
      }
      return player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, startTimeoutMs) === true ? "trance" : "unknown";
    };
    const meditateFor = (need) => {
      for (let attempt = 1; attempt <= attempts; attempt++) {
        if (!meditating()) {
          journal.clear();
          player.useSkill(Skills.Meditation);
          const outcome = startOutcome();
          if (outcome === "blocked" && stripMore2?.()) {
            log(`${prefix}: the trance was refused with armour on - took more off, trying again`);
            continue;
          }
          if (outcome === "blocked" || outcome === "unskilled") {
            refused = `the shard refuses meditation (${outcome})`;
            log(`${prefix}: ${refused} - check the off-hand; falling back on natural regeneration`);
            return watchMana(need, regenTimeoutMs);
          }
          if (outcome === "full") {
            return true;
          }
          if (outcome === "saving") {
            waitOutSave2();
          }
        }
        if (watchMana(need, timeoutMs)) {
          return true;
        }
        log(`${prefix}: meditation attempt ${attempt} did not fill the pool, using the skill again`);
      }
      return false;
    };
    return {
      manaTarget,
      blocked: () => unrestored,
      // Returns whether the mana actually arrived; what a failure means is the loop's to say.
      regainMana: (need) => {
        if (enough(need)) {
          return true;
        }
        log(`${prefix}: ${player.mana} mana, waiting for ${manaTarget(need)}`);
        const clearing = meditate && !refused;
        const clear = clearing && (stow2?.() ?? true);
        const arrived = clear ? meditateFor(need) : watchMana(need, regenTimeoutMs);
        if (clearing && restore2 && !restore2()) {
          unrestored = "could not get the weapon back in hand";
        }
        resetBeat2();
        return arrived;
      }
    };
  };

  // src/lib/skill.ts
  var tenths = (value) => (value / 10).toFixed(1);
  var createSkillReader = ({
    skill: skill2,
    label,
    timeoutMs,
    pollMs
  }) => {
    const value = () => player.getSkill(skill2)?.value;
    return {
      value,
      cap: () => player.getSkill(skill2)?.cap,
      name: () => player.getSkill(skill2)?.name ?? label,
      // The skill list arrives asynchronously, so a run that read it once would decide what to train
      // from whatever the client happened to know at paste time.
      waitForSkill: () => {
        for (let waited = 0; waited < timeoutMs; waited += pollMs) {
          const reading = value();
          if (reading !== void 0) {
            return reading;
          }
          sleep(pollMs);
        }
        return value();
      }
    };
  };

  // src/lib/die.ts
  var die = (reason) => {
    exit(reason);
    throw new Error(reason);
  };

  // src/lib/clock.ts
  var now = () => Date.now();

  // src/lib/loop.ts
  var backoffFor = (count, step, cap) => Math.min(step * count, cap);

  // src/lib/stages.ts
  var spellName = (spell) => Spells[spell] ?? `spell ${spell}`;
  var stageFor = (stages, value) => stages.find((stage) => value < stage.upTo);
  var orderedStages = (stages) => [...stages].sort((left, right) => left.upTo - right.upTo);
  var finalTarget = (stages) => stages.reduce((highest, stage) => Math.max(highest, stage.upTo), 0);
  var createPlan = (stages) => {
    const ordered = orderedStages(stages);
    return {
      stages: ordered,
      goal: finalTarget(ordered),
      stageNow: (value) => stageFor(ordered, value),
      describe: () => ordered.map((stage) => `${spellName(stage.spell)} to ${(stage.upTo / 10).toFixed(1)}`).join(", ")
    };
  };

  // src/lib/trainer.ts
  var TRAINED = "the last stage is finished";
  var runTrainer = ({
    prefix,
    stages,
    skill: skill2,
    castOnce: castOnce2,
    regainMana,
    manaBlocked,
    rearm,
    disabledIsProgress = false,
    stopReason: stopReason2,
    recover,
    beat: beat2,
    waitOutSave: waitOutSave2,
    preflight,
    timings
  }) => {
    const plan = createPlan(stages);
    if (plan.stages.length === 0) {
      die(`${prefix}: STAGES is empty - there is nothing to train`);
    }
    const start = skill2.waitForSkill() ?? die(`${prefix}: the client is not reporting the skill`);
    log(
      `${prefix}: ${skill2.name()} at ${tenths(start)}/${tenths(plan.goal)} - ${plan.describe()}`
    );
    preflight?.();
    const cap = skill2.cap();
    if (cap !== void 0 && plan.goal > cap) {
      log(
        `${prefix}: the last stage aims at ${tenths(plan.goal)} and the shard caps ${skill2.name()} at ${tenths(cap)} - it will not finish without a power scroll`
      );
    }
    const lostSomething = () => manaBlocked?.();
    const cycleCost = (stage) => Math.max(1, (stage.castTimeout ?? timings.castTimeout) + (stage.castDelay ?? timings.castDelay));
    const stalled = (idle, ceiling) => idle >= ceiling ? `${ceiling} cycles without a cast or a change in the skill` : void 0;
    let casts = 0;
    let fizzled = 0;
    let throttled = 0;
    let cooling = 0;
    let blind = 0;
    let unread = 0;
    let unreadPending = 0;
    let unreadSaid = false;
    let sinceProgress = 0;
    let lastValue = start;
    let reported = 0;
    let casting;
    let stop = plan.stageNow(start) ? void 0 : `${skill2.name()} is already at ${tenths(start)}`;
    for (let cycle = 0; cycle < timings.maxCycles && !stop; cycle++) {
      recover?.();
      stop = stopReason2();
      if (stop) {
        break;
      }
      const value = skill2.value();
      if (value === void 0) {
        blind++;
        if (blind >= timings.maxBlindReads) {
          stop = "the client stopped reporting the skill";
          break;
        }
        beat2("unreadable skill", cycle, casts);
        sleep(timings.stepDelay);
        continue;
      }
      blind = 0;
      if (value !== lastValue) {
        lastValue = value;
        sinceProgress = 0;
        casts += unreadPending;
        unreadPending = 0;
        unreadSaid = false;
      }
      const stage = plan.stageNow(value);
      if (!stage) {
        stop = TRAINED;
        break;
      }
      if (stage !== casting) {
        casting = stage;
        log(`${prefix}: ${tenths(value)} - ${spellName(stage.spell)} until ${tenths(stage.upTo)}`);
      }
      if (player.mana < stage.mana) {
        if (!regainMana(stage.mana)) {
          sinceProgress += Math.max(1, Math.round(timings.regenTimeout / cycleCost(stage)));
          log(`${prefix}: mana did not come back (${sinceProgress}/${timings.maxStale} idle)`);
        }
        stop = lostSomething() ?? stalled(sinceProgress, timings.maxStale);
        if (stop) {
          break;
        }
        beat2("recovering mana", cycle, casts);
        sleep(timings.stepDelay);
        continue;
      }
      const outcome = castOnce2(stage);
      if (outcome !== "throttled") {
        throttled = 0;
      }
      if (outcome !== "cooldown") {
        cooling = 0;
      }
      switch (outcome) {
        case "cast":
          casts++;
          sinceProgress = 0;
          unreadSaid = false;
          break;
        // Never counted towards a stop: Evasion spends most of its life on cooldown, and a run that
        // gave up after twenty of these would never finish the band that casts it.
        case "cooldown":
          cooling++;
          sinceProgress = 0;
          unreadSaid = false;
          sleep(backoffFor(cooling, timings.cooldownBackoff, timings.cooldownBackoffMax));
          break;
        // Counted rather than tallied - the shard charged nothing for it - but it clears the unknown
        // budget, because a fizzle is an outcome that was read and not one that was missed.
        case "fizzled":
          fizzled++;
          sinceProgress = 0;
          unreadSaid = false;
          break;
        case "alreadyUp":
          sinceProgress = 0;
          unreadSaid = false;
          sleep(timings.buffWait);
          break;
        // Waited out flat rather than backed off: a growing wait is for a shard that has to be
        // out-waited, and this is a spell that finishes on its own. Sharing the cooldown's backoff is
        // what made an eighth-circle band idle twenty seconds between casts.
        case "alreadyCasting":
          sinceProgress = 0;
          unreadSaid = false;
          sleep(timings.castingWait);
          break;
        case "disabled":
          sinceProgress = 0;
          unreadSaid = false;
          if (disabledIsProgress) {
            casts++;
            break;
          }
          log(`${prefix}: the shard toggled ${spellName(stage.spell)} off - check its buff in STAGES`);
          break;
        // The loop gathered mana before casting, so the stage's mana figure understates what it costs
        case "noMana":
          sinceProgress = 0;
          unreadSaid = false;
          log(
            `${prefix}: refused for mana at ${player.mana} - raise ${spellName(stage.spell)}'s mana in STAGES`
          );
          regainMana(stage.mana);
          break;
        // Nothing waited for fixes an empty pouch, and a run that carried on would spend the rest of
        // maxCycles casting nothing at all
        case "noReagents":
          stop = `out of reagents for ${spellName(stage.spell)}`;
          break;
        // Tithing points are gold given at a shrine, which is a walk and a gump away from this loop
        case "noTithing":
          stop = `out of tithing points for ${spellName(stage.spell)}`;
          break;
        // Most likely a draw that silently did not land after the last trance, which is recoverable
        case "noWeapon":
          sinceProgress = 0;
          unreadSaid = false;
          if (!rearm?.()) {
            stop = "the shard wants a weapon in hand and none could be drawn";
          }
          break;
        // The loop has no way out of the form: the spell that would leave it is the one being refused
        case "formLocked":
          stop = `the shard will not cast ${spellName(stage.spell)} in the form this character is in - that band cannot train itself`;
          break;
        case "unskilled":
          stop = `the shard says this character cannot use ${spellName(stage.spell)}`;
          break;
        // Every counter is reset, because whatever they had accumulated was measured against a server
        // that was not answering. The throttle and cooldown counts are cleared above with the rest.
        case "saving":
          waitOutSave2();
          sinceProgress = 0;
          unreadSaid = false;
          break;
        case "throttled":
          throttled++;
          sinceProgress = 0;
          unreadSaid = false;
          log(`${prefix}: shard says wait (${throttled}/${timings.maxThrottled}), backing off`);
          sleep(backoffFor(throttled, timings.throttleBackoff, timings.throttleBackoffMax));
          if (throttled >= timings.maxThrottled) {
            stop = "the shard kept refusing the cast";
          }
          break;
        // Not an ending, and not even a fault on its own. The commonest cause is a cast that worked
        // perfectly: a stage whose buff was already standing has no transition to show, so only the
        // mana can prove it, and a client that has not refreshed the figure yet leaves this loop with
        // nothing to read. The skill moving is what settles it, above.
        default:
          unread++;
          unreadPending++;
          sinceProgress++;
          if (!unreadSaid) {
            unreadSaid = true;
            log(`${prefix}: outcome unreadable - carrying on; check OUTCOME_TEXT if this run stalls`);
          }
      }
      stop = stop ?? lostSomething();
      if (stop) {
        break;
      }
      stop = stalled(sinceProgress, timings.maxStale);
      if (stop) {
        break;
      }
      if (casts >= reported + timings.logEvery) {
        reported = casts;
        log(
          `${prefix}: ${casts} casts, ${fizzled} fizzles, ${skill2.name()} at ${tenths(value)}/${tenths(plan.goal)}, ${player.mana} mana`
        );
      }
      beat2(outcome ?? "unknown", cycle, casts);
      sleep(stage.castDelay ?? timings.castDelay);
    }
    const reason = stop ?? `hit the ${timings.maxCycles} cycle backstop`;
    const ended = skill2.value();
    log(
      `${prefix}: ${casts} casts, ${fizzled} fizzles, ${skill2.name()} ${tenths(start)} -> ${ended === void 0 ? "unknown" : tenths(ended)}`
    );
    if (unread > 0) {
      log(`${prefix}: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
    }
    log(`${prefix}: stopping - ${reason}`);
    exit(`${prefix}: ${reason}`);
  };

  // src/lib/timings.ts
  var UNREACHABLE_DELAY = 5 * 60 * 1e3;
  var STEP_DELAY = 300;
  var TARGET_TIMEOUT = 2e3;
  var EQUIP_TIMEOUT = 2e3;
  var EQUIP_POLL = 200;
  var EQUIP_ATTEMPTS = 3;
  var MAX_CYCLES = 5e3;
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

  // src/necromancy/config.ts
  var SKILL = Skills.Necromancy;
  var SKILL_LABEL = "Necromancy";
  var STAGES = [
    // Cast at the character rather than at a creature, which would be a punchbag to find, keep alive
    // and keep in range. It costs health instead, which is what HURT_FLOOR is for.
    { upTo: 500, spell: Spells.PainSpike, mana: 5, buff: BuffDebuffs.PainSpike, target: "self" },
    { upTo: 700, spell: Spells.HorrificBeast, mana: 11, buff: BuffDebuffs.HorrificBeast },
    // No buff because the client publishes none for it - the mana leaving the pool is the proof. It is
    // also the one band that hits everything standing nearby.
    { upTo: 900, spell: Spells.Wither, mana: 23 },
    { upTo: 1e3, spell: Spells.LichForm, mana: 23, buff: BuffDebuffs.LichForm },
    { upTo: 1200, spell: Spells.VampiricEmbrace, mana: 23, buff: BuffDebuffs.VampiricEmbrace }
  ];
  var HURT_FLOOR = 0.5;
  var BANDAGE = true;
  var BANDAGE_GRAPHIC = 3617;
  var BANDAGE_ATTEMPTS = 4;
  var BANDAGE_TIMEOUT = 8e3;
  var HEAL_OUTCOME_TEXT = {
    healed: ["You finish applying the bandages", "You heal", "You apply the bandages"],
    // The pack search notices this first on most shards, so reaching it means bandages that vanished
    // between the search and the use.
    noBandages: [
      "You do not have a bandage",
      "You must have bandages",
      "You do not have any bandages"
    ],
    busy: ["You are already applying bandages"],
    interrupted: ["You have been interrupted"],
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };
  var SKILL_TIMEOUT = 1e3;
  var SKILL_POLL = 500;
  var MAX_BLIND_READS = 5;
  var CAST_TIMEOUT = 500;
  var CAST_DELAY = 500;
  var SKIP_WHEN_BUFFED = false;
  var DISABLED_IS_PROGRESS = true;
  var BUFF_WAIT = 2e3;
  var CASTING_WAIT = 750;
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
  var MAX_STALE = 200;
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
  var STRIP_MOVE_DELAY = 500;
  var STRIP_AT_ONCE = true;
  var DISARM_TIMEOUT = 2e3;
  var DISARM_POLL = 200;
  var DISARM_ATTEMPTS = 3;
  var OUTCOME_TEXT = {
    // Not depended on: the mana leaving the pool and the buff arriving are the proof
    cast: ["You are surrounded by a red aura", "You feel a sudden surge of power"],
    // The commonest outcome at a low skill. The shard charges nothing for it, which is why it reads as
    // silence to silentOutcome and has to be read from the words instead.
    fizzled: ["The spell fizzles", "You have failed to cast the spell"],
    noMana: ["You do not have enough mana", "Insufficient mana"],
    // The one refusal here that nothing waited for fixes
    noReagents: [
      "You do not have enough reagents",
      "More reagents are needed",
      "You lack the required reagents"
    ],
    alreadyUp: ["You are already under the effect"],
    // The transformation coming off, which is how the character leaves a form and half of what a form
    // band does. DISABLED_IS_PROGRESS is what tells the loop to count it rather than complain.
    disabled: ["You are no longer", "You return to your normal form", "You have disabled"],
    alreadyCasting: ["You are already casting a spell", "You are already casting"],
    // Horrific Beast is the one that does this on an OSI-faithful shard, and if the form spell itself
    // is refused then that band cannot train at all - worth being told once.
    formLocked: [
      "You cannot cast that spell in this form",
      "You can not cast this spell while polymorphed",
      "You cannot use that ability in this form"
    ],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: THROTTLED_TEXT
  };
  var MEDITATE_OUTCOME_TEXT = {
    trance: ["You enter a meditative trance."],
    full: ["You are at peace"],
    // Before unfocused, whose trailing full stop is deliberate: without it 'You cannot focus your
    // concentration' would also match the equipped-weapon sentence.
    //
    // This run stows nothing, so reaching this latches meditation off for the rest of the run and
    // falls back on natural regeneration. Start with empty hands.
    blocked: [
      "You cannot focus your concentration with an equipped weapon",
      "You cannot focus your concentration with an equipped shield",
      "You are preoccupied with thoughts of battle"
    ],
    // A failed roll or a trance broken by a hit - both fixed by using the skill again in a moment
    unfocused: ["You cannot focus your concentration.", "You lose your concentration"],
    unskilled: UNSKILLED_TEXT,
    saving: SAVING_TEXT,
    throttled: ["You must wait a few moments to use another skill", ...THROTTLED_TEXT]
  };

  // src/lib/entity.ts
  var hex = (value) => `0x${(value >>> 0).toString(16)}`;
  var describeItem = (item) => item ? `${hex(item.graphic)} '${item.name ?? ""}'` : "empty";

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

  // src/lib/gear.ts
  var createGear = (options) => {
    const { prefix } = options;
    const isHand = (layer) => layer === Layers.OneHanded || layer === Layers.TwoHanded;
    const hands = options.layers.filter(isHand);
    const rest = options.layers.filter((layer) => !isHand(layer));
    let stowed = [];
    let deep = options.stripAtOnce ?? false;
    const reported = /* @__PURE__ */ new Set();
    const wornOn = (layer) => client.findItemOnLayer(player.serial, layer);
    const off = (piece) => wornOn(piece.layer)?.serial !== piece.serial;
    const on = (piece) => wornOn(piece.layer)?.serial === piece.serial;
    const gone = (piece) => client.findObject(piece.serial) === void 0;
    const remember = (piece) => {
      if (!stowed.some((held) => held.serial === piece.serial)) {
        stowed.push(piece);
      }
    };
    const clearLayers = (targets, label) => {
      const worn = targets.map((layer) => ({ layer, item: wornOn(layer) })).filter((found) => found.item !== void 0);
      if (worn.length === 0) {
        return 0;
      }
      const pack = player.backpack?.serial;
      if (pack === void 0) {
        log(`${prefix}: nowhere to stow ${worn.length} piece(s) - the client reports no backpack`);
        return 0;
      }
      const pieces = worn.map(({ layer, item }) => ({
        serial: item.serial,
        layer,
        graphic: item.graphic,
        name: item.name
      }));
      pieces.forEach(remember);
      untilLanded({
        label,
        attempts: options.disarm.attempts,
        timeoutMs: options.disarm.timeoutMs,
        pollMs: options.disarm.pollMs,
        // Idempotent, because untilLanded reissues act() wholesale: without the skip a reissue would
        // bounce every piece that already landed back out of the pack and in again.
        act: () => {
          for (const piece of pieces) {
            if (off(piece)) {
              continue;
            }
            player.moveItem(piece.serial, pack);
            sleep(options.moveDelayMs);
          }
        },
        // Serial and not emptiness: if something else has landed on that layer, ours still came off
        landed: () => pieces.every(off)
      });
      return pieces.filter(off).length;
    };
    const handsClear = () => !hands.some((layer) => wornOn(layer) !== void 0);
    return {
      survey: () => {
        const worn = options.layers.map((layer) => wornOn(layer)).filter((item) => item !== void 0);
        if (worn.length === 0) {
          return "nothing on the strip layers - if the paperdoll disagrees, check STRIP_LAYERS";
        }
        return `${worn.length} piece(s) come off for a trance: ${worn.map(describeItem).join(", ")}`;
      },
      stow: () => {
        const targets = deep ? [...hands, ...rest] : hands;
        const label = deep ? "strip for the trance" : "stow what is in hand";
        clearLayers(targets, label);
        const clear = handsClear();
        if (!clear) {
          log(`${prefix}: could not clear both hands, so the trance will be refused`);
        }
        return clear;
      },
      stripMore: () => {
        if (deep) {
          return false;
        }
        const moved = clearLayers(rest, "strip the armour");
        deep = true;
        return moved > 0;
      },
      restore: () => {
        if (stowed.length === 0) {
          return true;
        }
        const wanted = [...stowed];
        target.cancel();
        untilLanded({
          label: "put the gear back on",
          attempts: options.equip.attempts,
          timeoutMs: options.equip.timeoutMs,
          pollMs: options.equip.pollMs,
          act: () => {
            for (const piece of wanted) {
              if (on(piece)) {
                continue;
              }
              player.equip(piece.serial);
              sleep(options.moveDelayMs);
            }
          },
          landed: () => wanted.every(on)
        });
        const missing = wanted.filter((piece) => !on(piece));
        const destroyed = new Set(missing.filter(gone).map((piece) => piece.serial));
        for (const piece of wanted) {
          if (on(piece)) {
            reported.delete(piece.serial);
          }
        }
        for (const piece of missing) {
          if (destroyed.has(piece.serial)) {
            log(`${prefix}: ${describeItem(piece)} ${hex(piece.serial)} is gone - not putting it back`);
          }
        }
        stowed = missing.filter((piece) => !destroyed.has(piece.serial));
        for (const piece of stowed) {
          if (!reported.has(piece.serial)) {
            reported.add(piece.serial);
            log(`${prefix}: ${describeItem(piece)} would not go back on - will try again next trance`);
          }
        }
        if (!handsClear()) {
          return true;
        }
        if (!wanted.some((piece) => isHand(piece.layer))) {
          return true;
        }
        if (options.rearm?.()) {
          return true;
        }
        return false;
      }
    };
  };

  // src/necromancy/gear.ts
  var gear = /* @__PURE__ */ createGear({
    prefix: "necro",
    layers: STRIP_LAYERS,
    moveDelayMs: STRIP_MOVE_DELAY,
    equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
    disarm: { attempts: DISARM_ATTEMPTS, timeoutMs: DISARM_TIMEOUT, pollMs: DISARM_POLL },
    stripAtOnce: STRIP_AT_ONCE
  });
  var { stow, stripMore, restore, survey } = gear;

  // src/lib/guards.ts
  var dead = () => player.isDead ? "you are dead" : void 0;
  var hurt = (fraction) => () => {
    const ceiling = hitsCeiling();
    if (ceiling === void 0) {
      return void 0;
    }
    return player.hits < ceiling * fraction ? `hurt (${player.hits}/${ceiling})` : void 0;
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

  // src/necromancy/guards.ts
  var floor = /* @__PURE__ */ hurt(HURT_FLOOR);
  var belowFloor = () => floor() !== void 0;
  var stopReason = () => firstReason(dead, floor);

  // src/lib/heal.ts
  var createBandager = ({
    prefix,
    graphic,
    outcomeText,
    timeoutMs,
    cursorTimeoutMs,
    attempts,
    recovered,
    waitOutSave: waitOutSave2
  }) => {
    const { all, outcomeFor } = outcomeVocabulary(outcomeText);
    let ranOut;
    const inPack = () => client.findType(graphic, void 0, player.backpack?.serial);
    const applyOnce = () => {
      const bandages = inPack();
      if (!bandages) {
        ranOut = "no bandages left in the pack";
        return false;
      }
      target.cancel();
      journal.clear();
      player.use(bandages.serial);
      if (!target.waitTargetSelf(cursorTimeoutMs)) {
        log(`${prefix}: no target cursor for the bandage`);
        return false;
      }
      const before = player.hits;
      const matched = journal.waitForTextAny(all, void 0, timeoutMs);
      const outcome = matched ? outcomeFor(matched) : void 0;
      if (outcome === "noBandages") {
        ranOut = "the shard says there are no bandages";
        return false;
      }
      if (outcome === "saving") {
        waitOutSave2();
      }
      return player.hits > before || outcome === "healed";
    };
    return {
      empty: () => ranOut,
      mend: () => {
        if (recovered()) {
          return true;
        }
        if (ranOut) {
          return false;
        }
        log(`${prefix}: ${player.hits}/${player.maxHits} hits, bandaging`);
        for (let attempt = 1; attempt <= attempts && !ranOut; attempt++) {
          applyOnce();
          if (recovered()) {
            log(`${prefix}: healed to ${player.hits}/${player.maxHits}`);
            return true;
          }
          if (player.isDead) {
            break;
          }
        }
        if (ranOut) {
          log(`${prefix}: ${ranOut}`);
        }
        return false;
      }
    };
  };

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

  // src/necromancy/heartbeat.ts
  var heartbeat = /* @__PURE__ */ createHeartbeat({
    prefix: "necro",
    noun: "casts",
    everyMs: HEARTBEAT_EVERY
  });
  var { beat, resetBeat } = heartbeat;

  // src/necromancy/save.ts
  var { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
    savingText: SAVING_TEXT,
    doneText: SAVE_DONE_TEXT,
    waitMs: SAVE_WAIT,
    pollMs: SAVE_POLL,
    stopReason,
    // This path reports on its own cadence, so the next beat starts a full interval from here
    onDone: resetBeat
  });

  // src/necromancy/heal.ts
  var bandager = /* @__PURE__ */ createBandager({
    prefix: "necro",
    graphic: BANDAGE_GRAPHIC,
    outcomeText: HEAL_OUTCOME_TEXT,
    timeoutMs: BANDAGE_TIMEOUT,
    cursorTimeoutMs: TARGET_TIMEOUT,
    attempts: BANDAGE_ATTEMPTS,
    recovered: () => !belowFloor(),
    waitOutSave
  });
  var mend = () => {
    if (!BANDAGE) {
      return;
    }
    bandager.mend();
  };
  var outOfBandages = bandager.empty;

  // src/necromancy/index.ts
  var PREFIX = "necro";
  var skill = createSkillReader({
    skill: SKILL,
    label: SKILL_LABEL,
    timeoutMs: SKILL_TIMEOUT,
    pollMs: SKILL_POLL
  });
  var { castOnce } = createCaster({
    outcomeText: OUTCOME_TEXT,
    timeoutMs: CAST_TIMEOUT,
    skipWhenBuffed: SKIP_WHEN_BUFFED
  });
  var mana = createManaWait({
    prefix: PREFIX,
    outcomeText: MEDITATE_OUTCOME_TEXT,
    meditate: MEDITATE,
    toFull: MEDITATE_TO_FULL,
    timeoutMs: MEDITATE_TIMEOUT,
    attempts: MEDITATE_ATTEMPTS,
    startTimeoutMs: MEDITATE_START_TIMEOUT,
    pollMs: MANA_POLL,
    logEveryMs: MANA_LOG_EVERY,
    regenTimeoutMs: REGEN_TIMEOUT,
    stow,
    restore,
    stripMore,
    stopReason,
    resetBeat,
    waitOutSave
  });
  runTrainer({
    prefix: PREFIX,
    stages: STAGES,
    skill,
    castOnce,
    regainMana: mana.regainMana,
    disabledIsProgress: DISABLED_IS_PROGRESS,
    stopReason,
    recover: mend,
    beat,
    waitOutSave,
    preflight: () => {
      log(
        `${PREFIX}: ${player.hits}/${player.maxHits} hits, ${player.mana}/${player.maxMana} mana`
      );
      log(`${PREFIX}: ${survey()}`);
      if (BANDAGE && !client.findType(BANDAGE_GRAPHIC, void 0, player.backpack?.serial)) {
        log(`${PREFIX}: no bandages in the pack - the health floor will stop the run instead`);
      }
    },
    timings: {
      castDelay: CAST_DELAY,
      castTimeout: CAST_TIMEOUT,
      buffWait: BUFF_WAIT,
      castingWait: CASTING_WAIT,
      stepDelay: STEP_DELAY,
      maxCycles: MAX_CYCLES,
      maxBlindReads: MAX_BLIND_READS,
      regenTimeout: REGEN_TIMEOUT,
      maxThrottled: MAX_THROTTLED,
      maxStale: MAX_STALE,
      logEvery: LOG_EVERY,
      cooldownBackoff: COOLDOWN_BACKOFF,
      cooldownBackoffMax: COOLDOWN_BACKOFF_MAX,
      throttleBackoff: THROTTLE_BACKOFF,
      throttleBackoffMax: THROTTLE_BACKOFF_MAX
    }
  });
})();
