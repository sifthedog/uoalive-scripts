import {
  LOCKPICK_FROM,
  LOG_EVERY,
  MAX_CYCLES,
  MAX_REOPENS,
  MAX_THROTTLED,
  MAX_UNKNOWN,
  RECIPES,
  isCalibrated,
  STEP_DELAY,
  STOP_AT,
  THROTTLE_BACKOFF,
  THROTTLE_BACKOFF_MAX,
  type RecipeName,
} from './config.js';
import { craftOnce } from './craft.js';
import { stopReason } from './guards.js';
import { ingotTotal } from './ingots.js';
import { currentPhase, skillBase, tenths } from './phase.js';
import { findTool, needsSwap } from './tool.js';

const uncalibrated = (Object.keys(RECIPES) as RecipeName[]).filter(
  (phase) => RECIPES[phase].category === undefined || RECIPES[phase].item === undefined,
);

const startedAt = skillBase();
log(`tinker: base ${tenths(startedAt)}, ${ingotTotal()} iron ingots in the pack`);

if (startedAt < LOCKPICK_FROM) {
  log(`tinker: base ${tenths(startedAt)} is under the ${tenths(LOCKPICK_FROM)} floor, making lockpicks anyway`);
}

let crafted = 0;
let failures = 0;
let unknown = 0;
let reopens = 0;
let throttled = 0;
let toolSerial: number | undefined;

// Seeding the loop's own stop flag rather than trusting exit() to halt, so an uncalibrated
// config can never reach reply() with an undefined button ID
let stop = uncalibrated.length
  ? `${uncalibrated.join(' and ')} button IDs are unset - run dist/tinker-probe.js and fill in config.js`
  : undefined;

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = stopReason();
  if (stop) {
    break;
  }

  const phase = currentPhase();
  if (phase === 'done') {
    stop = `base reached ${tenths(STOP_AT)}`;
    break;
  }

  if (needsSwap(toolSerial)) {
    toolSerial = findTool();
  }

  // needsSwap is true for a serial that is gone or missing, so this covers both the first cycle
  // and a swap that found nothing
  if (toolSerial === undefined) {
    stop = "out of tinker's tools";
    break;
  }

  const recipe = RECIPES[phase];

  // The pre-loop check already refuses to start uncalibrated; this narrows the button for the
  // compiler and keeps a hand-edited config from ever reaching reply() with an undefined ID
  if (!isCalibrated(recipe)) {
    stop = `${phase} has no button ID - run dist/tinker-probe.js and fill in config.ts`;
    break;
  }

  const outcome = craftOnce(recipe, toolSerial);

  switch (outcome) {
    case 'success':
    case 'used':
      crafted++;
      unknown = 0;
      reopens = 0;
      throttled = 0;
      break;

    case 'failed':
      failures++;
      unknown = 0;
      reopens = 0;
      throttled = 0;
      break;

    case 'wornOut':
      log(`tinker: tool worn out after ${crafted} ${recipe.label}s`);
      toolSerial = undefined;
      break;

    // Counted and backed off, not just slept through: a fixed retry shorter than the shard's own
    // timer re-arms the throttle it is waiting out, and the branch says nothing while it does it
    case 'throttled':
      throttled++;
      log(`tinker: shard says wait (${throttled}/${MAX_THROTTLED}), backing off`);
      sleep(Math.min(THROTTLE_BACKOFF * throttled, THROTTLE_BACKOFF_MAX));

      if (throttled >= MAX_THROTTLED) {
        stop = 'the shard kept refusing the craft';
      }
      break;

    case 'noGump':
      reopens++;
      log(`tinker: craft gump did not come back (${reopens}/${MAX_REOPENS})`);
      if (reopens >= MAX_REOPENS) {
        stop = 'the craft gump stopped opening';
      }
      break;

    case 'noMaterial':
      stop = 'out of iron ingots';
      break;

    default:
      unknown++;
      log(`tinker: nothing observable happened (${unknown}/${MAX_UNKNOWN})`);
      if (unknown >= MAX_UNKNOWN) {
        stop = 'no craft outcome could be detected - recheck OUTCOME_TEXT in config.js';
      }
  }

  if (crafted > 0 && crafted % LOG_EVERY === 0) {
    log(`tinker: ${crafted} made, ${failures} failed, base ${tenths(startedAt)} -> ${tenths(skillBase())}`);
  }

  sleep(STEP_DELAY);
}

log(`tinker: ${crafted} made, ${failures} failed, base ${tenths(startedAt)} -> ${tenths(skillBase())}, ${ingotTotal()} ingots left`);
exit(`tinker: ${stop ?? `hit the ${MAX_CYCLES} cycle backstop`}`);
