import { beforeEach, describe, expect, it } from 'vitest';
import { finalTarget, orderedStages, stageFor, type Stage } from './stages.js';
import { installGlobals } from '../test-support/uo.js';

// The stage table is the whole policy of a trainer, and every one of these runs with no client at
// all - which is the reason the table is in lib and the loop that uses it is not.

const BANDS: Stage[] = [
  { upTo: 600, spell: Spells.Confidence, mana: 10 },
  { upTo: 750, spell: Spells.CounterAttack, mana: 5 },
  { upTo: 1050, spell: Spells.Evasion, mana: 10 },
];

beforeEach(() => {
  installGlobals();
});

describe('stageFor', () => {
  it('picks the first band the value is under', () => {
    expect(stageFor(BANDS, 0)?.spell).toBe(Spells.Confidence);
    expect(stageFor(BANDS, 500)?.spell).toBe(Spells.Confidence);
    expect(stageFor(BANDS, 700)?.spell).toBe(Spells.CounterAttack);
    expect(stageFor(BANDS, 800)?.spell).toBe(Spells.Evasion);
  });

  // The bands are exclusive on upTo, so they butt together with no gap and no overlap: a value
  // sitting exactly on a bound has finished that band and belongs to the next one
  it('hands a value sitting exactly on a bound to the next band', () => {
    expect(stageFor(BANDS, 599)?.spell).toBe(Spells.Confidence);
    expect(stageFor(BANDS, 600)?.spell).toBe(Spells.CounterAttack);
    expect(stageFor(BANDS, 749)?.spell).toBe(Spells.CounterAttack);
    expect(stageFor(BANDS, 750)?.spell).toBe(Spells.Evasion);
    expect(stageFor(BANDS, 1049)?.spell).toBe(Spells.Evasion);
  });

  // The same call that picks a stage is the one that says the run is finished, which is the point of
  // asking one table both questions: a separate target constant could disagree with the last band
  it('answers with nothing once the last band has been passed', () => {
    expect(stageFor(BANDS, 1050)).toBeUndefined();
    expect(stageFor(BANDS, 1200)).toBeUndefined();
  });

  it('picks the first band for a value below every bound', () => {
    expect(stageFor(BANDS, -1)?.spell).toBe(Spells.Confidence);
  });

  // An empty table reads as finished, so the caller has to refuse it before the loop rather than run
  // a trainer that exits at once claiming success
  it('answers with nothing for an empty table', () => {
    expect(stageFor([], 0)).toBeUndefined();
  });

  it('takes the earlier of two rows sharing a bound', () => {
    const tied: Stage[] = [
      { upTo: 600, spell: Spells.Confidence, mana: 10 },
      { upTo: 600, spell: Spells.Evasion, mana: 10 },
    ];

    expect(stageFor(tied, 500)?.spell).toBe(Spells.Confidence);
  });
});

describe('orderedStages', () => {
  // find() takes the first row the value is under, so ascending order is its precondition. This is
  // what makes it a guarantee rather than something a config file is trusted to have got right.
  it('sorts a table written out of order', () => {
    const jumbled: Stage[] = [BANDS[2], BANDS[0], BANDS[1]];

    expect(orderedStages(jumbled).map((stage) => stage.upTo)).toEqual([600, 750, 1050]);
  });

  it('leaves an already ascending table alone', () => {
    expect(orderedStages(BANDS).map((stage) => stage.upTo)).toEqual([600, 750, 1050]);
  });

  it('returns a copy, so the config keeps the shape the file that wrote it says it has', () => {
    const jumbled: Stage[] = [BANDS[2], BANDS[0]];
    orderedStages(jumbled);

    expect(jumbled[0].upTo).toBe(1050);
  });
});

describe('finalTarget', () => {
  it('is the highest bound in the table', () => {
    expect(finalTarget(BANDS)).toBe(1050);
  });

  it('does not depend on the table being sorted', () => {
    expect(finalTarget([BANDS[2], BANDS[0]])).toBe(1050);
  });

  it('is 0 for an empty table', () => {
    expect(finalTarget([])).toBe(0);
  });
});
