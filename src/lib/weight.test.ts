import { beforeEach, describe, expect, it } from 'vitest';

import { installGlobals } from '../test-support/uo.js';
import { overweight } from './weight.js';

beforeEach(() => {
  installGlobals();
});

describe('overweight', () => {
  it('is true past the limit', () => {
    installGlobals({ player: { weight: 401, weightMax: 400 } });

    expect(overweight()).toBe(true);
  });

  it('is false at the limit exactly', () => {
    installGlobals({ player: { weight: 400, weightMax: 400 } });

    expect(overweight()).toBe(false);
  });

  it('brings the limit forward by the buffer it is given', () => {
    installGlobals({ player: { weight: 370, weightMax: 400 } });

    expect(overweight(40)).toBe(true);
    expect(overweight()).toBe(false);
  });

  // The client refreshes weight and weightMax independently and reports a max of 0 in between,
  // against which every weight in the game is over the limit - with a buffer, so is a weight of 0.
  it('is false while the client is reporting a max of zero', () => {
    installGlobals({ player: { weight: 436, weightMax: 0 } });

    expect(overweight()).toBe(false);
    expect(overweight(40)).toBe(false);
  });

  it('is false for an empty character mid-refresh, buffer or not', () => {
    installGlobals({ player: { weight: 0, weightMax: 0 } });

    expect(overweight(40)).toBe(false);
  });
});
