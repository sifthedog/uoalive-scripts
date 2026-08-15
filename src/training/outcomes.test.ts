import { beforeEach, describe, expect, it } from 'vitest';
import { createCaster } from '../lib/cast.js';
import { installGlobals } from '../test-support/uo.js';
import { CAST_TIMEOUT, OUTCOME_TEXT, SKIP_WHEN_BUFFED } from './config.js';

// The shipped Bushido phrase table, as opposed to src/lib/cast.test.ts which is about the mechanism

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

  // An ability on its own timer is not the shard refusing the run, and only one of the two is worth
  // giving up over. They are told apart by wording alone, so the wording is pinned.
  it('tells an ability cooldown apart from the action throttle', () => {
    expect(outcomeFor('You must wait before trying again')).toBe('cooldown');
    expect(outcomeFor('You must wait to perform another action')).toBe('throttled');
  });

  // waitForTextAny hands back whichever supplied string it found, and the cooldown sentence contains
  // the throttle's bare fallback - so the full wording has to be offered first or the client decides
  it('offers the cooldown wording before the bare throttle prefix', () => {
    expect(allText.indexOf('You must wait before trying again')).toBeLessThan(
      allText.indexOf('You must wait'),
    );
  });

  it('holds no duplicates, so a match is never ambiguous', () => {
    expect(new Set(allText).size).toBe(allText.length);
  });
});
