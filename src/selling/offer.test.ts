import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { VendorEntry } from './offer.js';

// The arithmetic itself is covered in src/lib/vendor.test.ts. What is left to prove here is the
// binding: that this reads KEEP out of this folder's config rather than some default. KEEP is 0 in
// the checked-in config, so it has to be mocked for the trim to run at all.
const withConfig = async (config: { KEEP: number }) => {
  vi.resetModules();
  vi.doMock('./config.js', () => config);
  return import('./offer.js');
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
});

describe('withKeepBack', () => {
  it('trims by the configured keep-back', async () => {
    const { withKeepBack } = await withConfig({ KEEP: 10 });

    const ingots: VendorEntry[] = [{ serial: 1, name: 'iron ingot', amount: 25 }];

    expect(withKeepBack(ingots)).toEqual([{ serial: 1, amount: 15 }]);
  });

  it('offers everything when nothing is kept back', async () => {
    const { withKeepBack } = await withConfig({ KEEP: 0 });

    expect(withKeepBack([{ serial: 1, name: 'iron ingot', amount: 25 }])).toEqual([
      { serial: 1, amount: 25 },
    ]);
  });

  // 'Leave ten behind' means ten of each, not ten between them, so a sale carrying several names
  // has to group before it trims - otherwise the second name pays for the first one's keep-back
  it('keeps back per name rather than across the offer', async () => {
    const { withKeepBack } = await withConfig({ KEEP: 10 });

    const mixed: VendorEntry[] = [
      { serial: 1, name: 'iron ingot', amount: 25 },
      { serial: 2, name: 'scimitar', amount: 12 },
    ];

    expect(withKeepBack(mixed)).toEqual([
      { serial: 1, amount: 15 },
      { serial: 2, amount: 2 },
    ]);
  });

  // Stacks of one name are trimmed as one pile however they are interleaved, and the request comes
  // back in the order the gump listed them
  it('spreads the keep-back across the stacks of one name, in gump order', async () => {
    const { withKeepBack } = await withConfig({ KEEP: 10 });

    const mixed: VendorEntry[] = [
      { serial: 1, name: 'iron ingot', amount: 4 },
      { serial: 2, name: 'scimitar', amount: 12 },
      { serial: 3, name: 'iron ingot', amount: 20 },
    ];

    expect(withKeepBack(mixed)).toEqual([
      { serial: 2, amount: 2 },
      { serial: 3, amount: 14 },
    ]);
  });
});
