import { finalTarget, orderedStages, type Stage } from '../lib/stages.js';
import { STAGES } from './config.js';

// The table sorted once, here, where it comes in from the config. stageFor takes the first row the
// value is under, so ascending order is its precondition rather than something a config file is
// trusted to have got right.
export const PLAN = /* @__PURE__ */ orderedStages(STAGES);

// What the run is aiming at, for the progress lines only. Whether it has arrived is stageNow coming
// back empty, so the two answers cannot disagree.
export const TARGET = /* @__PURE__ */ finalTarget(PLAN);

export const stageNow = (value: number): Stage | undefined =>
  PLAN.find((stage) => value < stage.upTo);

// The client's enums are real TypeScript enums, so they carry the reverse mapping and a spell can
// name itself. The fallback is for a value that is not in the enum at all, which costs one ugly log
// line rather than a crash.
export const spellName = (spell: Spells): string => Spells[spell] ?? `spell ${spell}`;

// Printed once at start-up, in the order the bands will actually be worked - so a config written out
// of order shows up in the first line of output rather than as a run training the wrong ability
export const describePlan = (): string =>
  PLAN.map((stage) => `${spellName(stage.spell)} to ${(stage.upTo / 10).toFixed(1)}`).join(', ');
