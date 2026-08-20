import { totalMatching } from '../lib/pack.js';
import { createTool } from '../lib/tool.js';
import {
  EQUIP_ATTEMPTS,
  EQUIP_POLL,
  EQUIP_TIMEOUT,
  LOCKPICK_GRAPHICS,
  LOCKPICK_NAME,
} from './config.js';

const tool = /* @__PURE__ */ createTool({
  label: 'lockpicks',
  name: LOCKPICK_NAME,
  graphics: LOCKPICK_GRAPHICS,

  // Used out of the pack rather than worn, so no layer answers for them and equip() is never called
  held: () => undefined,

  equip: { attempts: EQUIP_ATTEMPTS, timeoutMs: EQUIP_TIMEOUT, pollMs: EQUIP_POLL },
});

export const findLockpick = tool.find;

// Sums `amount`, so a stack of a hundred counts as a hundred rather than as one
export const lockpickTotal = (): number => totalMatching(tool.is);
