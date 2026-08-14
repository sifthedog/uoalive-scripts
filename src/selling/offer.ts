import {
  withKeepBack as trimTo,
  type SellRequestItem,
  type VendorEntry,
} from '../lib/vendor.js';
import { KEEP } from './config.js';

export type { SellRequestItem, VendorEntry };

export const withKeepBack = (matches: VendorEntry[]): SellRequestItem[] => trimTo(matches, KEEP);
