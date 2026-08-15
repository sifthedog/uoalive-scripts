import { beforeEach, describe, expect, it } from 'vitest';
import { createCaster } from '../lib/cast.js';
import { installGlobals } from '../test-support/uo.js';
import { CAST_TIMEOUT, OUTCOME_TEXT, SKIP_WHEN_BUFFED } from './config.js';

// The shipped Chivalry phrase table, as opposed to src/lib/cast.test.ts which is about the mechanism

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

  // The bucket this script is likeliest to end on, and the reason it is not left to MAX_UNKNOWN
  it('has a wording for running out of tithing points', () => {
    expect(OUTCOME_TEXT.noTithing?.length).toBeGreaterThan(0);
    expect(outcomeFor('You do not have enough tithing points')).toBe('noTithing');
  });

  // Karma is not a bucket of its own: a character without it cannot cast these at all, which is what
  // unskilled means and what stopping is the right answer to
  it('reads a karma refusal as unskilled', () => {
    expect(outcomeFor('Your karma is not high enough')).toBe('unskilled');
  });

  // waitForTextAny hands back whichever supplied string it found, and the throttle's bare fallback is
  // short enough to be contained by a longer sentence - so the longer ones are offered first
  it('offers the already-casting wording before the bare throttle prefix', () => {
    expect(allText.indexOf('You are already casting a spell')).toBeLessThan(
      allText.indexOf('You must wait'),
    );
  });

  // No reagents to run out of, no cooldown of their own, and no form to be locked in
  it('writes down no bucket this run cannot reach', () => {
    expect(OUTCOME_TEXT.noReagents).toBeUndefined();
    expect(OUTCOME_TEXT.cooldown).toBeUndefined();
    expect(OUTCOME_TEXT.formLocked).toBeUndefined();
  });
});
