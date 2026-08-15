// Casts through a table of stages until the last one is passed. Everything the shipped trainers
// disagree about comes in through the call - nothing here reads a config.

import type { CastOutcome } from './cast.js';
import { die } from './die.js';
import { backoffFor } from './loop.js';
import type { SkillReader } from './skill.js';
import { tenths } from './skill.js';
import { createPlan, spellName, type Stage } from './stages.js';

export interface TrainerTimings {
  // Pacing rather than a wait: an ability with a cooldown of its own refuses a cast that comes too
  // early, and a loop with no pause re-arms that timer every retry. The default for a row that does
  // not carry its own castDelay.
  castDelay: number;

  // The caster's own figure, which this loop never waits on itself - it is here only so the weighting
  // below can price a casting cycle, and castOnce stands in this window on every cast that the shard
  // says nothing about.
  castTimeout: number;

  // Not a backoff - the buff expires on its own schedule and nothing the run does hurries it.
  buffWait: number;

  // Flat and short: unlike a throttle there is nothing here to out-wait, only the cast in flight.
  castingWait: number;

  stepDelay: number;
  maxCycles: number;

  // Counted apart from maxStale: a client that has gone quiet about a skill is not an outcome the
  // script failed to read, and it should not spend that budget.
  maxBlindReads: number;

  // Only ever used to weigh a dry mana stretch against a casting cycle - see sinceProgress
  regenTimeout: number;

  maxThrottled: number;

  // Casting cycles that produced neither a readable cast nor any movement in the skill, before the
  // run gives up. This is the budget an unreadable outcome spends, and it is deliberately generous:
  // the thing worth ending a run over is a script that is getting nowhere, and an outcome this loop
  // cannot read is not that. A wrong OUTCOME_TEXT on a run that is training anyway is a log problem.
  maxStale: number;

  logEvery: number;

  // The ceiling is well above the throttle's on purpose: that one is sized for an action throttle
  // measured in seconds, this for an ability that can be most of a minute between uses.
  cooldownBackoff: number;
  cooldownBackoffMax: number;

  throttleBackoff: number;
  throttleBackoffMax: number;
}

export interface TrainerOptions {
  prefix: string;

  stages: Stage[];
  skill: SkillReader;

  castOnce: (stage: Stage) => CastOutcome | undefined;
  regainMana: (need: number) => boolean;

  // The mana wait reporting it could not put back what it stowed - the one thing that half of a run
  // can discover that has to end this one. Absent for a script that stows nothing.
  manaBlocked?: () => string | undefined;

  // Absent for a script whose spells need no weapon, which is also one whose OUTCOME_TEXT has no
  // noWeapon phrases, so the branch that uses this cannot be reached at all.
  rearm?: () => boolean;

  // For a stacking move a toggle-off is a cast paid for and thrown away; for a transformation it is
  // how the character leaves the form, and it rolls the skill and charges mana like any other cast.
  disabledIsProgress?: boolean;

  stopReason: () => string | undefined;

  // Runs before the guards judge the character, at the top of every cycle: the guard that would stop
  // the run is the same one that says it is hurt, so the mending has to come first.
  recover?: () => void;

  beat: (phase: string, cycle: number, tally: number) => void;
  waitOutSave: () => void;

  preflight?: () => void;

  timings: TrainerTimings;
}

const TRAINED = 'the last stage is finished';

export const runTrainer = ({
  prefix,
  stages,
  skill,
  castOnce,
  regainMana,
  manaBlocked,
  rearm,
  disabledIsProgress = false,
  stopReason,
  recover,
  beat,
  waitOutSave,
  preflight,
  timings,
}: TrainerOptions): void => {
  const plan = createPlan(stages);

  if (plan.stages.length === 0) {
    die(`${prefix}: STAGES is empty - there is nothing to train`);
  }

  // Polled for rather than assumed: the skill list arrives asynchronously, and a run that read a
  // blind client as 0 would cast the first band's ability at a character who has capped the skill.
  const start = skill.waitForSkill() ?? die(`${prefix}: the client is not reporting the skill`);

  log(
    `${prefix}: ${skill.name()} at ${tenths(start)}/${tenths(plan.goal)} - ${plan.describe()}`,
  );

  preflight?.();

  // Said rather than corrected: a scroll may be on its way, and a run that quietly retargeted itself
  // would be lying about its plan.
  const cap = skill.cap();

  if (cap !== undefined && plan.goal > cap) {
    log(
      `${prefix}: the last stage aims at ${tenths(plan.goal)} and the shard caps ` +
        `${skill.name()} at ${tenths(cap)} - it will not finish without a power scroll`,
    );
  }

  const lostSomething = (): string | undefined => manaBlocked?.();

  // What one casting cycle of a row actually costs in wall clock, and the denominator the dry-stretch
  // weighting below is priced against. castDelay alone is the wrong figure twice over: it leaves out
  // the window castOnce stands in - which a successful cast spends all of, because success is the
  // outcome no table has a wording for - and on a table with per-row figures it is not even this
  // row's pause. Priced on castDelay alone at 750, one dry stretch was charged 160 of a 200 ceiling
  // and two of them ended a run that was training perfectly well.
  const cycleCost = (stage: Stage): number =>
    Math.max(1, (stage.castTimeout ?? timings.castTimeout) + (stage.castDelay ?? timings.castDelay));

  // The one ending left that is about the run getting nowhere, said in one place because two paths
  // reach it - a cast the loop could not read, and a mana stretch that brought nothing back.
  const stalled = (idle: number, ceiling: number): string | undefined =>
    idle >= ceiling ? `${ceiling} cycles without a cast or a change in the skill` : undefined;

  let casts = 0;
  let fizzled = 0;
  let throttled = 0;

  // No ceiling on this one, because being on cooldown is not a fault.
  let cooling = 0;
  let blind = 0;

  // Outcomes this loop could not read. Reported at the end so a wrong OUTCOME_TEXT is still obvious,
  // but never a reason to stop on its own: whether the run is getting anywhere is a separate question
  // from whether it can follow along, and the skill answers it.
  let unread = 0;

  // The ones since the skill last moved, credited to the cast tally when it does. A cast the loop
  // could not read is still a cast if the skill went up because of it.
  let unreadPending = 0;

  // Said once per stretch rather than once per cast: eight lines about one condition is how a real
  // ending gets lost in the scroll.
  let unreadSaid = false;

  // Cycles that produced neither a readable cast nor any movement in the skill. The only counter left
  // that can end a run, and it covers what maxUnknown and maxHungry used to do separately: a wrong
  // OUTCOME_TEXT on a run going nowhere, and a pool that never comes back, look identical from here -
  // nothing is happening - and identical is how they should be treated.
  let sinceProgress = 0;

  // The last figure the client gave for the skill, so movement can be spotted between cycles. Seeded
  // from the start-up read rather than from 0, which would read as a gain on the first cycle.
  let lastValue = start;

  // The tally at the last progress line, rather than `casts % logEvery` - that is a property of the
  // count and not of the cycle, so it stays true for every cycle after the twenty-fifth cast.
  let reported = 0;

  // Which stage the last line was about, so a change of ability is announced once rather than per cycle
  let casting: Stage | undefined;

  // Set rather than exited on, so the one tail below reports every ending there is.
  let stop: string | undefined = plan.stageNow(start)
    ? undefined
    : `${skill.name()} is already at ${tenths(start)}`;

  for (let cycle = 0; cycle < timings.maxCycles && !stop; cycle++) {
    recover?.();

    stop = stopReason();

    if (stop) {
      break;
    }

    const value = skill.value();

    // A client that has stopped answering is a blip, not an ending: read as 0 it trains a capped
    // character, read as finished it ends a good run. So it is counted, on a budget of its own.
    if (value === undefined) {
      blind++;

      if (blind >= timings.maxBlindReads) {
        stop = 'the client stopped reporting the skill';
        break;
      }

      beat('unreadable skill', cycle, casts);
      sleep(timings.stepDelay);
      continue;
    }

    blind = 0;

    // The proof that cannot be argued with, and the one this loop was missing. Every other signal is
    // circumstantial - a wording the table may have wrong, a buff that was already up before the
    // cast, a mana figure the client had not refreshed yet - and a run can be training perfectly well
    // while all three stay silent. If the number moved, the casting is working, whatever it looked
    // like from in here. Either direction counts: a skill falling because another one is gaining is
    // still the shard telling us it is processing these casts.
    if (value !== lastValue) {
      lastValue = value;
      sinceProgress = 0;

      // Credited now rather than guessed at earlier: these were casts, and the gain is what says so
      casts += unreadPending;
      unreadPending = 0;
      unreadSaid = false;
    }

    // The same table that picks the ability answers whether there is one left, so the two cannot
    // disagree the way a separate target constant would.
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
      // A stretch that brought nothing back is a cycle that got nowhere, counted on the same budget
      // as an unreadable one rather than on a ceiling of its own. There is no separate ending for it
      // any more: a pool that never returns and a table that cannot read a cast both show up here as
      // a run that is not training, and one counter says so once.
      if (!regainMana(stage.mana)) {
        // Weighted, because the two paths that reach this counter cost wildly different amounts of
        // wall clock: a cast cycle is cycleCost, and a mana stretch that brought nothing back has
        // just spent the whole regenTimeout standing still. Counting both as one would either end a
        // slow-gaining run in minutes or leave a mana-starved one going for hours. Charged for what
        // it cost, one dry stretch is worth however many casting cycles fit inside it.
        sinceProgress += Math.max(1, Math.round(timings.regenTimeout / cycleCost(stage)));

        log(`${prefix}: mana did not come back (${sinceProgress}/${timings.maxStale} idle)`);
      }

      // A trance that could not give the weapon back leaves a character who can neither cast nor
      // fight, which is the one thing the mana half is allowed to end the run over.
      stop = lostSomething() ?? stalled(sinceProgress, timings.maxStale);

      if (stop) {
        break;
      }

      beat('recovering mana', cycle, casts);
      sleep(timings.stepDelay);
      continue;
    }

    const outcome = castOnce(stage);

    // Both are consecutive counts - the backoffs grow with them and the ceiling reads one as "the
    // shard has refused twenty in a row" - so both are cleared by any cycle that was not the thing
    // they count. Cleared here rather than in each branch that is not a throttle or a cooldown,
    // because that is what the branches were doing and three of them forgot: an unread outcome, a
    // cast still in flight and a refusal for mana all left the counts standing. On a run whose
    // successes are unreadable nothing ever cleared them, so twenty throttles spread over hours -
    // never two together - ended a run the shard was not refusing at all.
    if (outcome !== 'throttled') {
      throttled = 0;
    }

    if (outcome !== 'cooldown') {
      cooling = 0;
    }

    switch (outcome) {
      case 'cast':
        casts++;
        sinceProgress = 0;
        unreadSaid = false;
        break;

      // Never counted towards a stop: Evasion spends most of its life on cooldown, and a run that
      // gave up after twenty of these would never finish the band that casts it.
      case 'cooldown':
        cooling++;
        sinceProgress = 0;
        unreadSaid = false;
        sleep(backoffFor(cooling, timings.cooldownBackoff, timings.cooldownBackoffMax));
        break;

      // Counted rather than tallied - the shard charged nothing for it - but it clears the unknown
      // budget, because a fizzle is an outcome that was read and not one that was missed.
      case 'fizzled':
        fizzled++;
        sinceProgress = 0;
        unreadSaid = false;
        break;

      case 'alreadyUp':
        sinceProgress = 0;
        unreadSaid = false;
        sleep(timings.buffWait);
        break;

      // Waited out flat rather than backed off: a growing wait is for a shard that has to be
      // out-waited, and this is a spell that finishes on its own. Sharing the cooldown's backoff is
      // what made an eighth-circle band idle twenty seconds between casts.
      case 'alreadyCasting':
        sinceProgress = 0;
        unreadSaid = false;
        sleep(timings.castingWait);
        break;

      case 'disabled':
        sinceProgress = 0;
        unreadSaid = false;

        if (disabledIsProgress) {
          // A transformation coming off: the shard rolled the skill and charged the mana, so it is a
          // cast. A run through a form band is half of these by design, so it is not logged.
          casts++;
          break;
        }

        // The toggle went the other way on a move that was supposed to stack, so the buff gate is
        // not seeing this ability. Said every time, because each one is a cast thrown away.
        log(`${prefix}: the shard toggled ${spellName(stage.spell)} off - check its buff in STAGES`);
        break;

      // The loop gathered mana before casting, so the stage's mana figure understates what it costs
      case 'noMana':
        sinceProgress = 0;
        unreadSaid = false;
        log(
          `${prefix}: refused for mana at ${player.mana} - raise ` +
            `${spellName(stage.spell)}'s mana in STAGES`,
        );
        regainMana(stage.mana);
        break;

      // Nothing waited for fixes an empty pouch, and a run that carried on would spend the rest of
      // maxCycles casting nothing at all
      case 'noReagents':
        stop = `out of reagents for ${spellName(stage.spell)}`;
        break;

      // Tithing points are gold given at a shrine, which is a walk and a gump away from this loop
      case 'noTithing':
        stop = `out of tithing points for ${spellName(stage.spell)}`;
        break;

      // Most likely a draw that silently did not land after the last trance, which is recoverable
      case 'noWeapon':
        sinceProgress = 0;
        unreadSaid = false;

        if (!rearm?.()) {
          stop = 'the shard wants a weapon in hand and none could be drawn';
        }
        break;

      // The loop has no way out of the form: the spell that would leave it is the one being refused
      case 'formLocked':
        stop =
          `the shard will not cast ${spellName(stage.spell)} in the form this character is in - ` +
          `that band cannot train itself`;
        break;

      case 'unskilled':
        stop = `the shard says this character cannot use ${spellName(stage.spell)}`;
        break;

      // Every counter is reset, because whatever they had accumulated was measured against a server
      // that was not answering. The throttle and cooldown counts are cleared above with the rest.
      case 'saving':
        waitOutSave();
        sinceProgress = 0;
        unreadSaid = false;
        break;

      case 'throttled':
        throttled++;
        sinceProgress = 0;
        unreadSaid = false;
        log(`${prefix}: shard says wait (${throttled}/${timings.maxThrottled}), backing off`);
        sleep(backoffFor(throttled, timings.throttleBackoff, timings.throttleBackoffMax));

        if (throttled >= timings.maxThrottled) {
          stop = 'the shard kept refusing the cast';
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

    // Asked with ?? rather than assigned: a plain assignment here is what the script this was
    // extracted from did, and it threw away every `stop` the switch had just set - `unskilled` and
    // the twentieth throttle both ended in a run that carried on regardless.
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
        `${prefix}: ${casts} casts, ${fizzled} fizzles, ${skill.name()} at ` +
          `${tenths(value)}/${tenths(plan.goal)}, ${player.mana} mana`,
      );
    }

    beat(outcome ?? 'unknown', cycle, casts);
    sleep(stage.castDelay ?? timings.castDelay);
  }

  const reason = stop ?? `hit the ${timings.maxCycles} cycle backstop`;
  const ended = skill.value();

  // A delta rather than a figure, because a trainer that cast four hundred times and moved nothing
  // has failed loudly. The fizzle count rides along because the two together are the run's real rate.
  log(
    `${prefix}: ${casts} casts, ${fizzled} fizzles, ${skill.name()} ${tenths(start)} -> ` +
      `${ended === undefined ? 'unknown' : tenths(ended)}`,
  );

  // Said only when there were any, and said last so it reads as the footnote it is: the run was fine,
  // the table needs a line adding. Silence here means OUTCOME_TEXT covered everything the shard said.
  if (unread > 0) {
    log(`${prefix}: ${unread} outcome(s) went unread - add the shard's wording to OUTCOME_TEXT`);
  }

  // Said through log as well as handed to exit, because how the client renders an exit message is
  // its own business and the reason a run ended must not be the line that gets away
  log(`${prefix}: stopping - ${reason}`);
  exit(`${prefix}: ${reason}`);
};
