import { RING_FROM, STOP_AT, type RecipeName } from './config.js';

// base, not value: value includes +Tinkering from jewelry, so a ring falling off mid-run would
// read as a skill drop and a +15 ring would read as an early finish.
export const skillBase = (): number => player.getSkill(Skills.Tinkering)?.base ?? 0;

export const tenths = (value: number): string => (value / 10).toFixed(1);

export const currentPhase = (): RecipeName | 'done' => {
  const base = skillBase();

  if (base >= STOP_AT) {
    return 'done';
  }
  if (base >= RING_FROM) {
    return 'rings';
  }
  return 'lockpicks';
};
