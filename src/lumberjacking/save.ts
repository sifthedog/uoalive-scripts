import { SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT } from './config.js';
import { stopReason } from './guards.js';
import { resetBeat } from './heartbeat.js';

// A world save is a pause, not a fault. The shard stops answering for several seconds while it
// writes its world file, and everything attempted in that window is refused: the swing sends no
// cursor, the journal answers with none of the harvest wordings, the pack diff a conversion is
// judged by never moves, and an animal takes nothing. Every one of those looks exactly like a
// failure of the thing being attempted - an unreadable outcome, a wood that cannot be worked, a
// full pack animal - and each is remembered for the rest of the run. Waiting is the whole fix.
//
// A copy of src/mining/save.ts, reading this folder's own wordings, the same way walk.ts and
// guards.ts are copies. It was found on a mining run; this script had the identical gap.

export const isSaving = (): boolean => SAVING_TEXT.some((text) => journal.containsText(text));

export const waitOutSave = (): void => {
  log('save: the world is saving, waiting it out');

  // Cleared first so the completion line has to arrive *after* this point: the message that got us
  // here is still sitting in the journal, and on a shard that words both ends of the save alike a
  // stale line would end the wait before the save did.
  journal.clear();

  // Sliced rather than slept through in one go, so the client stays responsive and the guards still
  // get a look in. The timeout is the fallback for a shard whose completion wording SAVE_DONE_TEXT
  // does not have: standing still for SAVE_WAIT is the cost of missing it, which is survivable.
  for (let waited = 0; waited < SAVE_WAIT; waited += SAVE_POLL) {
    sleep(SAVE_POLL);

    if (SAVE_DONE_TEXT.some((text) => journal.containsText(text))) {
      break;
    }

    // Left to the caller to report and act on, so the wait has one way out and the run has one
    if (stopReason()) {
      return;
    }
  }

  // This path reports on its own cadence, so the next beat starts a full interval from here
  resetBeat();
};
