// Trains a skill by casting the ability that still gains at the level the skill has reached, working
// through a table of stages and stopping when the last one is passed. Bushido out of the box; the
// table in config.ts is the whole policy, so another skill is another table rather than another
// script.
//
// The two halves of the run want opposite things from the character's hands - these are weapon
// abilities, and meditation is refused while anything is equipped - so the weapon is stowed for every
// trance and drawn again before the next cast. See weapon.ts.

import { die } from '../lib/die.js';
import { describeItem } from '../lib/entity.js';
import { backoffFor } from '../lib/loop.js';
import type { Stage } from '../lib/stages.js';
import { castOnce } from './cast.js';
import {
  BUFF_WAIT,
  CAST_DELAY,
  COOLDOWN_BACKOFF,
  COOLDOWN_BACKOFF_MAX,
  LOG_EVERY,
  MAX_BLIND_READS,
  MAX_CYCLES,
  MAX_HUNGRY,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  STEP_DELAY,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
} from './config.js';
import { stopReason } from './guards.js';
import { beat } from './heartbeat.js';
import { regainMana, weaponLost } from './meditate.js';
import { PLAN, TARGET, describePlan, spellName, stageNow } from './plan.js';
import { waitOutSave } from './save.js';
import { skillCap, skillName, skillValue, tenths, waitForSkill } from './skill.js';
import { held, rearm, rememberWeapon } from './weapon.js';

// The ending this script is written for, named because the summary has to tell it apart from the
// several endings that mean something went wrong
const TRAINED = 'the last stage is finished';

if (PLAN.length === 0) {
  die('train: STAGES is empty - there is nothing to train');
}

// Polled for rather than assumed: the skill list arrives asynchronously like everything else, and a
// run that opened by reading a blind client as 0 would cast the first band's ability at a character
// who has capped the skill
const start = waitForSkill() ?? die('train: the client is not reporting the skill');

// Learned from what is actually in hand, so the draw after each trance matches on this weapon's
// graphic rather than on whatever WEAPON_NAME happens to find in the pack
const weapon = held();
rememberWeapon(weapon);

log(`train: ${skillName()} at ${tenths(start)}/${tenths(TARGET)} - ${describePlan()}`);
log(`train: hand ${describeItem(weapon)}, ${player.mana}/${player.maxMana} mana`);

if (!weapon) {
  log('train: nothing in hand - these are weapon abilities, so the first cast may be refused');
}

// The shard's own cap, against a table that may be aiming past it. Said rather than corrected: a 105
// scroll may be on its way, and a run that quietly retargeted itself would be lying about its plan.
const cap = skillCap();

if (cap !== undefined && TARGET > cap) {
  log(
    `train: the last stage aims at ${tenths(TARGET)} and the shard caps ` +
      `${skillName()} at ${tenths(cap)} - it will not finish without a power scroll`,
  );
}

let casts = 0;
let fizzled = 0;
let unknown = 0;
let throttled = 0;

// Consecutive refusals on an ability's own cooldown. Grows the wait and nothing else - there is no
// ceiling on it, because being on cooldown is not a fault.
let cooling = 0;
let hungry = 0;
let blind = 0;

// The tally at the last progress line, rather than `casts % LOG_EVERY` - that is a property of the
// count and not of the cycle, so it stays true for every cycle after the twenty-fifth cast
let reported = 0;

// Which stage the last line was about, so a change of ability is announced once rather than per cycle
let casting: Stage | undefined;

// The run is over before it starts if the skill is already past the last band. Set rather than exited
// on, so the one tail below does the reporting for every ending there is.
let stop: string | undefined = stageNow(start)
  ? undefined
  : `${skillName()} is already at ${tenths(start)}`;

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();

  if (stop) {
    break;
  }

  const value = skillValue();

  // A client that has stopped answering for a skill it was answering a moment ago is a blip, not an
  // ending. Read as 0 it trains a capped character, and read as finished it ends a good run, so it is
  // neither: it is counted, on a budget of its own.
  if (value === undefined) {
    blind++;

    if (blind >= MAX_BLIND_READS) {
      stop = 'the client stopped reporting the skill';
      break;
    }

    beat('unreadable skill', cycle, casts);
    sleep(STEP_DELAY);
    continue;
  }

  blind = 0;

  // The same table that picks the ability answers whether there is one left, so the two cannot
  // disagree the way a separate target constant would
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
        stop = 'the mana never came back';
        break;
      }
    }

    // A trance that could not give the weapon back leaves a character who cannot cast and cannot
    // fight, which is the one thing the mana half is allowed to end the run over
    stop = weaponLost();

    if (stop) {
      break;
    }

    beat('recovering mana', cycle, casts);
    sleep(STEP_DELAY);
    continue;
  }

  const outcome = castOnce(stage);

  switch (outcome) {
    case 'cast':
      casts++;
      unknown = 0;
      throttled = 0;
      cooling = 0;
      break;

    // The ability's own timer, which is it working as designed rather than the shard refusing the
    // run. Never counted towards a stop for that reason: Evasion spends most of its life on cooldown,
    // and a run that gave up after twenty of these would never finish the band that casts it.
    case 'cooldown':
      cooling++;
      unknown = 0;
      throttled = 0;
      sleep(backoffFor(cooling, COOLDOWN_BACKOFF, COOLDOWN_BACKOFF_MAX));
      break;

    // A failed casting roll, which is ordinary and gets commoner the lower the skill is. Counted
    // rather than tallied - the shard charged nothing for it and no ability went up - but it clears
    // the unknown budget, because a fizzle is an outcome that was read and not one that was missed.
    case 'fizzled':
      fizzled++;
      unknown = 0;
      throttled = 0;
      cooling = 0;
      break;

    // Not a fault and not progress: the ability is standing and will drop on its own schedule
    case 'alreadyUp':
      unknown = 0;
      sleep(BUFF_WAIT);
      break;

    // The toggle went the other way, which means the buff gate is not seeing this ability at all.
    // Said every time it happens, because each one is a cast paid for and thrown away.
    case 'disabled':
      unknown = 0;
      log(`train: the shard toggled ${spellName(stage.spell)} off - check its buff in STAGES`);
      break;

    // The loop gathered mana before casting, so the stage's mana figure is understating what it costs
    case 'noMana':
      unknown = 0;
      log(
        `train: refused for mana at ${player.mana} - raise ` +
          `${spellName(stage.spell)}'s mana in STAGES`,
      );
      regainMana(stage.mana);
      break;

    // Most likely a draw that silently did not land after the last trance, which is recoverable -
    // stopping outright would end a good run over one dropped item move
    case 'noWeapon':
      unknown = 0;

      if (!rearm()) {
        stop = 'the shard wants a weapon in hand and none could be drawn';
      }
      break;

    case 'unskilled':
      stop = `the shard says this character cannot use ${spellName(stage.spell)}`;
      break;

    // Nothing was learned and nothing went wrong: the shard was writing its world file. Every counter
    // is reset, because whatever they had accumulated was measured against a server that was not
    // answering.
    case 'saving':
      waitOutSave();
      unknown = 0;
      throttled = 0;
      break;

    case 'throttled':
      throttled++;
      unknown = 0;
      log(`train: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(backoffFor(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the cast';
      }
      break;

    default:
      unknown++;
      log(`train: unreadable outcome (${unknown}/${MAX_UNKNOWN}), check OUTCOME_TEXT`);
  }

  // The noMana branch waits for mana too, so the weapon can be lost on this path as well as on the
  // one above. Asked once here, after every branch that could have meditated.
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
      `train: ${casts} casts, ${fizzled} fizzles, ${skillName()} at ` +
        `${tenths(value)}/${tenths(TARGET)}, ${player.mana} mana`,
    );
  }

  beat(outcome ?? 'unknown', cycle, casts);
  sleep(CAST_DELAY);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;
const ended = skillValue();

// The gain is the whole point of the run, so it is the summary - and it is a delta rather than a
// figure, because a trainer that cast four hundred times and moved nothing has failed loudly
// The fizzle count rides along with the gain because the two together are the run's real rate: a
// character who fizzles most of what it casts is training at a fraction of the speed the cast tally
// suggests, and there is nothing in the loop that would otherwise say so
log(
  `train: ${casts} casts, ${fizzled} fizzles, ${skillName()} ${tenths(start)} -> ` +
    `${ended === undefined ? 'unknown' : tenths(ended)}`,
);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`train: stopping - ${reason}`);
exit(`train: ${reason}`);
