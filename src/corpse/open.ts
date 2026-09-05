import { contentsOf, forgetUnreadable } from '../lib/containers.js';
import { isMobile } from '../lib/entity.js';
import { artKey } from '../lib/sift.js';

export type OpenOutcome = 'opened' | 'empty' | 'unreadable' | 'gone';

export interface Opened {
  outcome: OpenOutcome;
  contents: Item[];
}

export interface OpenDelays {
  openDelay: number;
  settlePoll: number;
  settleTimeout: number;
}

const corpseAt = (serial: number): Item | undefined => {
  const found = client.findObject(serial);

  return found && !isMobile(found) ? found : undefined;
};

// Never openContainers: 0x2006 is deliberately kept out of CONTAINER_GRAPHICS so the pack searches
// in the other scripts do not start double-clicking corpses.
export const open = (serial: number, delays: OpenDelays): Opened => {
  player.use(serial);
  sleep(delays.openDelay);

  // Opening a container is what makes it readable, so a throw latched on the way in is cleared
  forgetUnreadable(serial);

  let contents = contentsOf(corpseAt(serial));

  // Polled rather than slept through: the answer usually arrives inside OPEN_DELAY, and the timeout
  // is only paid by a corpse that never answers at all.
  for (
    let waited = 0;
    waited < delays.settleTimeout && contents === undefined;
    waited += delays.settlePoll
  ) {
    sleep(delays.settlePoll);
    forgetUnreadable(serial);
    contents = contentsOf(corpseAt(serial));
  }

  // Before 'empty': a corpse that decayed inside the wait is not an empty one
  if (!corpseAt(serial)) {
    return { outcome: 'gone', contents: [] };
  }

  if (contents === undefined) {
    return { outcome: 'unreadable', contents: [] };
  }

  return { outcome: contents.length ? 'opened' : 'empty', contents };
};

export const describeHeld = (contents: Item[], limit: number): string => {
  if (contents.length === 0) {
    return 'nothing';
  }

  const totals = new Map<string, number>();

  for (const item of contents) {
    const key = (item.name ?? '').trim() || artKey(item);
    totals.set(key, (totals.get(key) ?? 0) + (item.amount ?? 1));
  }

  const listed = [...totals].slice(0, limit).map(([key, count]) => `${key} x${count}`);
  const left = totals.size - listed.length;

  return listed.join(', ') + (left > 0 ? `, and ${left} more` : '');
};
