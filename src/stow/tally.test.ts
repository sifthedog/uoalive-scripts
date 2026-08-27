import { describe, expect, it } from 'vitest';

import { createQuiet, verdictFor } from './tally.js';

describe('verdictFor', () => {
  it('reads nothing to move as the watch working', () => {
    expect(verdictFor(0, 0)).toBe('idle');
  });

  it('reads a pass that shifted some of what it issued as progress', () => {
    expect(verdictFor(4, 1)).toBe('moved');
  });

  it('reads a pass that issued moves and shifted nothing as quiet', () => {
    expect(verdictFor(4, 0)).toBe('quiet');
  });
});

describe('createQuiet', () => {
  it('never ends a run that has had nothing to move', () => {
    const quiet = createQuiet(3);

    for (let cycle = 0; cycle < 20; cycle++) {
      quiet.saw('idle');
    }

    expect(quiet.reason(0)).toBeUndefined();
  });

  it('counts only the passes that moved nothing', () => {
    const quiet = createQuiet(3);

    expect(quiet.saw('quiet')).toBe(1);
    expect(quiet.saw('idle')).toBe(1);
    expect(quiet.saw('quiet')).toBe(2);
  });

  it('starts over when something lands', () => {
    const quiet = createQuiet(3);

    quiet.saw('quiet');
    quiet.saw('quiet');

    expect(quiet.saw('moved')).toBe(0);
    expect(quiet.reason(9)).toBeUndefined();
  });

  it('starts over when a save is sat out', () => {
    const quiet = createQuiet(2);

    quiet.saw('quiet');
    quiet.reset();

    expect(quiet.saw('quiet')).toBe(1);
    expect(quiet.reason(9)).toBeUndefined();
  });

  it('names the count and what is left when it gives up', () => {
    const quiet = createQuiet(2);

    quiet.saw('quiet');
    expect(quiet.reason(9)).toBeUndefined();

    quiet.saw('quiet');
    expect(quiet.reason(9)).toBe('2 passes in a row moved nothing, with 9 still in the pack');
  });
});
