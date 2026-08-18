import { createThreatWatch } from '../lib/threat.js';
import {
  ATTACK_TEXT,
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
import { findBeetle } from './smelt.js';

// findBeetle and not smeltAll: dist/mine-here.js contains no player.run at all, and that promise is
// a property of the file rather than of the loop.
export const watchForTrouble = (prefix: string): (() => void) | undefined =>
  WATCH_FOR_TROUBLE
    ? createThreatWatch({
        prefix,
        range: THREAT_RANGE,
        hostile: HOSTILE_NOTORIETY,
        companion: findBeetle,
        companionName: 'beetle',
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
