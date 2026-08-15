// A skill trained by casting: which ability to cast is a property of where the skill has got to, and
// the gain from any one of them dries up long before the skill caps. The table is the whole policy -
// one row per band, each naming the value it trains up to - and both questions the loop asks are
// answered off it: which ability now, and whether there is anything left to do. Asking them of one
// table is the point; a separate target constant is a second place for the last band to be wrong.
//
// Nothing here reads the client or a config. The table comes in through the call, so the decisions
// are testable with no globals at all, and a second skill is a second table rather than a second
// script.

export interface Stage {
  // The value this band trains up to, in the tenths getSkill reports: 74.6 arrives as 746, so 600 is
  // 60.0. Exclusive, so the bands butt together with no gap and no overlap - a skill sitting exactly
  // on a bound has finished that band and belongs to the next one.
  upTo: number;

  spell: Spells;

  // What the shard charges for it, and so the figure the loop gathers mana up to before it casts. A
  // value set too low shows up as a noMana outcome, which says so; too high costs a little sitting
  // still and nothing else.
  mana: number;

  // The buff the ability puts up, where the shard publishes one. It does two jobs: it stops the run
  // re-issuing an ability that is already standing, and it is the proof a cast landed that does not
  // depend on how this shard words its journal. Optional, because neither is true everywhere - a row
  // without it still trains, on the mana it spent alone.
  buff?: BuffDebuffs;
}

// The band a value falls in, or undefined once the last one has been passed - which is the same
// question as "is this run finished", asked of the same rows.
//
// This is the if/else chain the script started as, and the chain's real fault was not its length: it
// was that the bounds, their order and their exhaustiveness were spread over the branches, so a typo
// in one of them (105 where 1050 was meant) read as a perfectly ordinary branch that never ran.
//
// find() takes the first row the value is under, so the rows have to be in ascending order of upTo.
// orderedStages is how that is guaranteed rather than assumed.
export const stageFor = (stages: Stage[], value: number): Stage | undefined =>
  stages.find((stage) => value < stage.upTo);

// A sorted copy, taken once where the table comes in. Sorted here rather than inside stageFor so that
// stays a plain find() and the ordering is paid for once a run instead of once a cycle; copied rather
// than sorted in place so a config's array keeps the shape the file that wrote it says it has.
export const orderedStages = (stages: Stage[]): Stage[] =>
  [...stages].sort((left, right) => left.upTo - right.upTo);

// What the run is aiming at, for the lines that report progress - never for deciding it has arrived.
// That is stageFor coming back empty, so the two answers cannot disagree.
export const finalTarget = (stages: Stage[]): number =>
  stages.reduce((highest, stage) => Math.max(highest, stage.upTo), 0);
