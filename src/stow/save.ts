import { createSaveWatch } from '../lib/save.js';
import { SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT, SAVING_TEXT } from './config.js';
import { stopReason } from './guards.js';
import { resetBeat } from './heartbeat.js';

export const { isSaving, waitOutSave } = /* @__PURE__ */ createSaveWatch({
  savingText: SAVING_TEXT,
  doneText: SAVE_DONE_TEXT,
  waitMs: SAVE_WAIT,
  pollMs: SAVE_POLL,
  stopReason,
  onDone: resetBeat,
});
