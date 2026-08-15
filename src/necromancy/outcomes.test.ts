import { beforeEach, describe, expect, it } from 'vitest';
import { createCaster } from '../lib/cast.js';
import { installGlobals } from '../test-support/uo.js';
import { CAST_TIMEOUT, OUTCOME_TEXT, SKIP_WHEN_BUFFED } from './config.js';

// The shipped Necromancy phrase table, as opposed to src/lib/cast.test.ts which is about the mechanism

beforeEach(() => {
  installGlobals();
});

const { allText, outcomeFor } = createCaster({
  outcomeText: OUTCOME_TEXT,
  timeoutMs: CAST_TIMEOUT,
  skipWhenBuffed: SKIP_WHEN_BUFFED,
});

describe('OUTCOME_TEXT', () => {
  // Table-driven off the config itself, so adding a phrase without wiring up its category is caught
  // here rather than showing up in game as an 'unknown' outcome
  for (const [name, phrases] of Object.entries(OUTCOME_TEXT)) {
    for (const phrase of phrases ?? []) {
      it(`maps '${phrase}' to ${name}`, () => {
        expect(outcomeFor(phrase)).toBe(name);
      });
    }
  }

  it('does not recognise a phrase from another shard', () => {
    expect(outcomeFor('You feel a strange sensation')).toBeUndefined();
  });

  it('holds no duplicates, so a match is never ambiguous', () => {
    expect(new Set(allText).size).toBe(allText.length);
  });

  // The two buckets this table has and the weapon trainer's does not. An empty pouch read as an
  // unknown outcome costs five cycles and blames the wrong thing.
  it('has a wording for an empty pouch and for a form that will not cast', () => {
    expect(OUTCOME_TEXT.noReagents?.length).toBeGreaterThan(0);
    expect(OUTCOME_TEXT.formLocked?.length).toBeGreaterThan(0);
  });

  // Nothing here needs a weapon in hand, and no necromancy spell has a cooldown of its own. Left in,
  // those buckets would only be phrases waiting to match something else by accident.
  it('writes down no bucket this run cannot reach', () => {
    expect(OUTCOME_TEXT.noWeapon).toBeUndefined();
    expect(OUTCOME_TEXT.cooldown).toBeUndefined();
  });
});
