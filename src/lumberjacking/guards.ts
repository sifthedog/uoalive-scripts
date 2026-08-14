import { dead, firstReason, heavy, packFull, type Guard } from '../lib/guards.js';
import { describeBounds, inBounds } from './bounds.js';
import { PACK_LIMIT, WEIGHT_BUFFER } from './config.js';

// Every step is checked before it is taken, so this only trips if something else moved the
// character - a teleporter, a boat, a GM - or if the run started outside the box. Local to this
// folder because only this folder has a box.
const insideBounds: Guard = () =>
  inBounds(player.x, player.y)
    ? undefined
    : `at ${player.x},${player.y}, outside ${describeBounds()}`;

// Anything here ends the run cleanly; the loop asks before every chop
export const stopReason = (): string | undefined =>
  firstReason(dead, insideBounds, heavy(WEIGHT_BUFFER), packFull(PACK_LIMIT));
