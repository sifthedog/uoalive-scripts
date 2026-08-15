// The stage table: which ability to cast is a property of where the skill has got to. Both questions
// the loop asks are answered off one table - which ability now, and whether there is anything left -
// so a separate target constant cannot disagree with the last band.

export interface Stage {
  // In the tenths getSkill reports: 74.6 arrives as 746, so 600 is 60.0. Exclusive, so a skill
  // sitting exactly on a bound has finished that band and belongs to the next one.
  upTo: number;

  spell: Spells;

  // What the shard charges, and so the figure the loop gathers mana up to before it casts
  mana: number;

  // Where the shard publishes one. It stops the run re-issuing an ability that is already standing,
  // and is the proof a cast landed that does not depend on how this shard words its journal.
  buff?: BuffDebuffs;

  // 'self' is player.castTo(spell, player). Absent is the ordinary case: a weapon ability, a
  // self-transformation and an area attack are all cast at nobody.
  target?: 'self';
}

// The client's enums are real TypeScript enums, so they carry the reverse mapping. The fallback is
// for a value that is not in the enum at all.
export const spellName = (spell: Spells): string => Spells[spell] ?? `spell ${spell}`;

// Undefined once the last band has been passed, which is the same question as "is this run
// finished". find() takes the first row the value is under, so the rows must be in ascending order
// of upTo - orderedStages is how that is guaranteed rather than assumed.
export const stageFor = (stages: Stage[], value: number): Stage | undefined =>
  stages.find((stage) => value < stage.upTo);

// Sorted here rather than inside stageFor so that stays a plain find() and the ordering is paid for
// once a run; copied rather than sorted in place so a config's array keeps the shape it was written in.
export const orderedStages = (stages: Stage[]): Stage[] =>
  [...stages].sort((left, right) => left.upTo - right.upTo);

// For the progress lines, never for deciding the run has arrived - that is stageFor coming back
// empty, so the two answers cannot disagree.
export const finalTarget = (stages: Stage[]): number =>
  stages.reduce((highest, stage) => Math.max(highest, stage.upTo), 0);

export interface Plan {
  // Ascending, which is stageFor's precondition and is settled here rather than trusted to the config
  stages: Stage[];

  goal: number;

  stageNow: (value: number) => Stage | undefined;

  // In the order the bands will actually be worked, so a table written out of order shows up in the
  // first line of output rather than as a run training the wrong ability
  describe: () => string;
}

export const createPlan = (stages: Stage[]): Plan => {
  const ordered = orderedStages(stages);

  return {
    stages: ordered,
    goal: finalTarget(ordered),
    stageNow: (value) => stageFor(ordered, value),
    describe: () =>
      ordered.map((stage) => `${spellName(stage.spell)} to ${(stage.upTo / 10).toFixed(1)}`).join(', '),
  };
};
