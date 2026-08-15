import { describe, expect, it } from 'vitest';

import { SELL_AT, SELL_AT_SLOTS } from './config.js';
import { reasonToSell } from './trigger.js';

describe('reasonToSell', () => {
  it('keeps watching while both thresholds are short', () => {
    expect(reasonToSell(SELL_AT - 1, SELL_AT_SLOTS - 1)).toBeUndefined();
  });

  it('sells once enough of the item has piled up', () => {
    expect(reasonToSell(SELL_AT, 0)).toBe(`${SELL_AT} held`);
  });

  // The threshold is the point it fires, not the point it has been passed
  it('fires on the threshold rather than past it', () => {
    expect(reasonToSell(SELL_AT, 0)).toBeDefined();
    expect(reasonToSell(SELL_AT + 5, 0)).toBeDefined();
  });

  // A pack filling with something else still needs the room the watched item is taking
  it('sells early when the pack is running out of slots', () => {
    expect(reasonToSell(1, SELL_AT_SLOTS)).toBe(`${SELL_AT_SLOTS} pack slots used`);
  });

  // Firing here would say 'vendor sell' every poll for as long as the pack stayed full, and free
  // nothing each time, because none of what is filling it is what this run is watching
  it('does not sell on a full pack holding none of the item', () => {
    expect(reasonToSell(0, SELL_AT_SLOTS + 10)).toBeUndefined();
  });

  it('reports the count rather than the slots when both are over', () => {
    expect(reasonToSell(SELL_AT, SELL_AT_SLOTS)).toBe(`${SELL_AT} held`);
  });
});
