import { describe, expect, it } from 'vitest';

import { ITEM_BUTTON } from './config.js';

describe('ITEM_BUTTON', () => {
  // The worked example from the config's own comment: lockpick as the 17th entry in Tools
  it('matches the worked example in the config comment', () => {
    expect(ITEM_BUTTON(17)).toBe(322);
  });

  it('starts the first row at 2', () => {
    expect(ITEM_BUTTON(1)).toBe(2);
  });

  it('steps by 20 a row', () => {
    expect(ITEM_BUTTON(2)).toBe(22);
    expect(ITEM_BUTTON(3)).toBe(42);
  });

  // Rows carry on across NEXT PAGE rather than restarting, so row 11 is the first of page two and
  // must not collide with row 1
  it('keeps counting across a page boundary', () => {
    expect(ITEM_BUTTON(11)).toBe(202);
    expect(ITEM_BUTTON(11)).not.toBe(ITEM_BUTTON(1));
  });
});
