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
});
