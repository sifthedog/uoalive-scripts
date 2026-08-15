import { beforeEach, describe, expect, it } from 'vitest';
import { createCaster } from '../lib/cast.js';
import { installGlobals } from '../test-support/uo.js';
import { CAST_TIMEOUT, OUTCOME_TEXT, SKIP_WHEN_BUFFED } from './config.js';

// The shipped Magery phrase table, as opposed to src/lib/cast.test.ts which is about the mechanism

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

  // The bucket this table expects to see most, because an eighth-circle cast is seconds long and the
  // loop asks again on a timer. It is not a fault, and the loop must not spend MAX_UNKNOWN on it.
  it('has a wording for a cast that came in before the last one finished', () => {
    expect(outcomeFor('You are already casting a spell')).toBe('alreadyCasting');
  });

  // waitForTextAny hands back whichever supplied string it found, and the throttle's bare fallback is
  // short enough to be contained by a longer sentence - so the longer ones are offered first
  it('offers the already-casting wording before the bare throttle prefix', () => {
    expect(allText.indexOf('You are already casting a spell')).toBeLessThan(
      allText.indexOf('You must wait'),
    );
  });

  // Magery is the second skill here that consumes something
  it('has a wording for an empty reagent pouch', () => {
    expect(OUTCOME_TEXT.noReagents?.length).toBeGreaterThan(0);
  });

  // No weapon, no cooldown, no form, and tithing is the paladin's currency
  it('writes down no bucket this run cannot reach', () => {
    expect(OUTCOME_TEXT.noWeapon).toBeUndefined();
    expect(OUTCOME_TEXT.cooldown).toBeUndefined();
    expect(OUTCOME_TEXT.formLocked).toBeUndefined();
    expect(OUTCOME_TEXT.noTithing).toBeUndefined();
  });
});
