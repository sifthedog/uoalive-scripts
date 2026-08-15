import { dead, firstReason, packFull } from '../lib/guards.js';
import { PACK_LIMIT } from './config.js';

// No box check: mining roams, and the one this folder started with was lumberjacking's forest, which
// stopped every run on cycle zero.
//
// No weight check either: being over the limit is what triggers the smelt, so a guard at a buffer
// below it would fire first every time and the smelt would never happen. The loop stops on weight
// itself, after smelting has had its turn and freed nothing.
export const stopReason = (): string | undefined => firstReason(dead, packFull(PACK_LIMIT));
