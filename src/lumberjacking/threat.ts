import { createThreatWatch } from '../lib/threat.js';
import {
  ATTACK_TEXT,
  CALL_ON_SIGHT_NOTORIETY,
  GUARD_CALL,
  GUARD_CALLS,
  GUARD_CALL_DELAY,
  GUARD_REPLY_WAIT,
  GUARD_ZONE_TEXT,
  HOSTILE_NOTORIETY,
  NO_GUARDS_TEXT,
  THREAT_RANGE,
  UNGUARDED_TEXT,
  WATCH_FOR_TROUBLE,
} from './config.js';
import { findPackAnimals } from './haul.js';

// The nearest animal only: findPackAnimals sorts by distance, and one of the herd losing health is
// the same news as all of them.
export const watchForTrouble = WATCH_FOR_TROUBLE
  ? createThreatWatch({
      prefix: 'lumberjack',
      range: THREAT_RANGE,
      hostile: HOSTILE_NOTORIETY,
      callOnSight: CALL_ON_SIGHT_NOTORIETY,
      companion: () => findPackAnimals()[0],
      companionName: 'pack animal',
      call: GUARD_CALL,
      calls: GUARD_CALLS,
      callDelay: GUARD_CALL_DELAY,
      replyWait: GUARD_REPLY_WAIT,
      noGuardsText: NO_GUARDS_TEXT,
      attackText: ATTACK_TEXT,
      guardedText: GUARD_ZONE_TEXT,
      unguardedText: UNGUARDED_TEXT,
    }).check
  : undefined;
