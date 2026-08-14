import { describe, expect, it } from 'vitest';

import { outcomeVocabulary } from './outcomes.js';

const OUTCOME_TEXT = {
  chopped: ['You put', 'You hack at the tree'],
  empty: ["There's not enough wood here to harvest"],
  throttled: ['You must wait to perform another action', 'You must wait'],
};

const { all, outcomeFor } = outcomeVocabulary(OUTCOME_TEXT);

describe('outcomeVocabulary', () => {
  // journal.waitForTextAny takes one array, so every phrase in every bucket has to be in it
  it('flattens every bucket into one list to wait on', () => {
    expect(all).toHaveLength(5);
    expect(all).toContain('You put');
    expect(all).toContain('You must wait');
  });

  it('maps a matched phrase back to its bucket', () => {
    expect(outcomeFor('You hack at the tree')).toBe('chopped');
    expect(outcomeFor("There's not enough wood here to harvest")).toBe('empty');
  });

  // waitForTextAny hands back one of the strings it was given, so this cannot really miss - but the
  // callers keep the maybe rather than asserting it away
  it('has nothing to say about a phrase it was never given', () => {
    expect(outcomeFor('You feel a strange breeze')).toBeUndefined();
  });

  // Bucket order decides between two phrases close enough to both match, which is worth knowing
  // when adding one: the bare 'You must wait' prefix is kept last for exactly this reason
  it('answers with the first bucket that claims the phrase', () => {
    const { outcomeFor: pick } = outcomeVocabulary({
      first: ['shared phrase'],
      second: ['shared phrase'],
    });

    expect(pick('shared phrase')).toBe('first');
  });
});
