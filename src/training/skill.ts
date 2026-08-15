import { SKILL, SKILL_LABEL, SKILL_POLL, SKILL_TIMEOUT } from './config.js';

// Every read of getSkill goes through here, because the client's own typings declare it returning
// undefined and the whole script turns on what that is taken to mean.

// The client's tenths as a person reads them: 746 is 74.6
export const tenths = (value: number): string => (value / 10).toFixed(1);

// Never coerced to 0. 0 is a real skill value, and reading a blind client as 0 makes the trainer cast
// the first band's ability at a character who has capped the skill - so the maybe is passed on and
// every caller is made to say what it does about it.
export const skillValue = (): number | undefined => player.getSkill(SKILL)?.value;

export const skillCap = (): number | undefined => player.getSkill(SKILL)?.cap;

// The shard's own name for it once the skill list has arrived, and the configured label until then
export const skillName = (): string => player.getSkill(SKILL)?.name ?? SKILL_LABEL;

// The skill list arrives asynchronously like everything else, so a run that opened by reading it once
// would decide what to train from whatever the client happened to know at paste time. Polled, and the
// common case - a list that arrived long ago - costs one read.
export const waitForSkill = (): number | undefined => {
  for (let waited = 0; waited < SKILL_TIMEOUT; waited += SKILL_POLL) {
    const value = skillValue();

    if (value !== undefined) {
      return value;
    }

    sleep(SKILL_POLL);
  }

  return skillValue();
};
