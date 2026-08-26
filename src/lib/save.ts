// A world save is a pause, not a fault. The shard stops answering for several seconds and everything
// attempted in that window is refused - the swing sends no cursor, the pack diff never moves, an
// animal takes nothing - each of which looks exactly like a failure of the thing being attempted and
// is remembered for the rest of the run. Found on a mining run after five 'unreadable outcome'
// cycles ended it.

export interface SaveWatch {
  isSaving: () => boolean;
  waitOutSave: () => void;
}

export const createSaveWatch = (options: {
  savingText: string[];
  doneText: string[];
  waitMs: number;
  pollMs: number;
  stopReason: () => string | undefined;
  onDone: () => void;
}): SaveWatch => ({
  isSaving: () => options.savingText.some((text) => journal.containsText(text)),

  waitOutSave: () => {
    log('save: the world is saving, waiting it out');

    const said = (texts: string[]): boolean => texts.some((text) => journal.containsText(text));

    // Read *before* the clear. A save can start and finish inside one swing - a dig alone waits up
    // to DIG_TIMEOUT - so by the time this runs the completion is usually already in the journal.
    // Clearing first threw it away and then stood still for the whole of waitMs, once per save.
    let ended = said(options.doneText) ? 'the shard had already finished' : undefined;

    // Cleared so a completion has to arrive after this point: the line that got us here is still in
    // the journal, and the last save's completion would otherwise end this one's wait.
    journal.clear();

    // Sliced rather than slept through, so the client stays responsive and the guards get a look in.
    // The timeout is the fallback for a shard whose completion wording doneText does not have.
    for (let waited = 0; !ended && waited < options.waitMs; waited += options.pollMs) {
      sleep(options.pollMs);

      if (said(options.doneText)) {
        ended = 'the shard says it is done';
      } else if (options.stopReason()) {
        // Left to the caller to report and act on, so the wait has one way out and the run has one
        ended = 'the run has a reason to stop';
      }
    }

    // Always said: without a closing line the run goes quiet at 'waiting it out' and there is no way
    // to tell a save that ended from one that was never noticed.
    log(`save: ${ended ?? `nothing said in ${Math.round(options.waitMs / 1000)}s`}, carrying on`);

    options.onDone();
  },
});
