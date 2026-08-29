import { beforeEach, describe, expect, it } from 'vitest';
import { createCaster } from '../lib/cast.js';
import { installGlobals } from '../test-support/uo.js';
import { CAST_TIMEOUT, OUTCOME_TEXT } from './config.js';

beforeEach(() => {
  installGlobals();
});

const { allText, outcomeFor } = createCaster({
  outcomeText: OUTCOME_TEXT,
  timeoutMs: CAST_TIMEOUT,
  skipWhenBuffed: true,
});

describe('OUTCOME_TEXT', () => {
  // Table-driven off the config itself, so adding a phrase without wiring up its category is caught
  // here rather than showing up in game as a miss
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

  // The two refusals that retire an entry rather than retrying it
  it('has a wording for running out of tithing points and for being refused outright', () => {
    expect(outcomeFor('You do not have enough tithing points')).toBe('noTithing');
    expect(outcomeFor('You are not skilled enough')).toBe('unskilled');
  });

  // 'You must wait' is a substring of the longer throttle wordings, so bucket order decides this
  it('reads a cast already in flight as that rather than as the action throttle', () => {
    expect(outcomeFor('You are already casting a spell')).toBe('alreadyCasting');
    expect(outcomeFor('You must wait')).toBe('throttled');
  });
});
