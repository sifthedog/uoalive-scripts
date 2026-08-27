import { describe, expect, it } from 'vitest';

import { createPace } from './pace.js';

const pacing = () => createPace({ floor: 1000, step: 400, max: 2000, easeAfter: 3 });

describe('createPace', () => {
  it('starts at the floor', () => {
    expect(pacing().delay()).toBe(1000);
  });

  it('adds a step for every refusal', () => {
    const pace = pacing();

    expect(pace.refused()).toBe(1400);
    expect(pace.refused()).toBe(1800);
  });

  // The shard's timer is finite; a pace that climbed forever would sit out a blip for the rest of
  // the run
  it('climbs no further than the cap', () => {
    const pace = pacing();

    for (let refusal = 0; refusal < 10; refusal++) {
      pace.refused();
    }

    expect(pace.delay()).toBe(2000);
  });

  // Easing on the first success walks straight back into the refusal it just escaped, and a run
  // spends half its cycles alternating between the two
  it('holds the pace until a stretch of reads has landed', () => {
    const pace = pacing();
    pace.refused();

    expect(pace.landed()).toBe(1400);
    expect(pace.landed()).toBe(1400);
    expect(pace.landed()).toBe(1000);
  });

  it('starts the stretch again after a refusal in the middle of one', () => {
    const pace = pacing();
    pace.refused();
    pace.landed();
    pace.landed();
    pace.refused();

    expect(pace.landed()).toBe(1800);
    expect(pace.landed()).toBe(1800);
    expect(pace.landed()).toBe(1400);
  });

  it('never eases below the floor', () => {
    const pace = pacing();

    for (let landed = 0; landed < 20; landed++) {
      pace.landed();
    }

    expect(pace.delay()).toBe(1000);
  });
});
