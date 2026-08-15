// Every read of player.getSkill goes through a reader built here, because the client's own typings
// declare it returning undefined and a trainer turns entirely on what that is taken to mean.

export interface SkillReaderOptions {
  skill: Skills;

  // Used in the log lines until the skill list arrives and getSkill has a name of its own
  label: string;

  timeoutMs: number;
  pollMs: number;
}

export interface SkillReader {
  value: () => number | undefined;
  cap: () => number | undefined;
  name: () => string;
  waitForSkill: () => number | undefined;
}

// The client's tenths as a person reads them: 746 is 74.6
export const tenths = (value: number): string => (value / 10).toFixed(1);

export const createSkillReader = ({
  skill,
  label,
  timeoutMs,
  pollMs,
}: SkillReaderOptions): SkillReader => {
  // Never coerced to 0. 0 is a real skill value, and reading a blind client as 0 makes the trainer
  // cast the first band's ability at a character who has capped the skill.
  const value = (): number | undefined => player.getSkill(skill)?.value;

  return {
    value,
    cap: () => player.getSkill(skill)?.cap,

    name: () => player.getSkill(skill)?.name ?? label,

    // The skill list arrives asynchronously, so a run that read it once would decide what to train
    // from whatever the client happened to know at paste time.
    waitForSkill: () => {
      for (let waited = 0; waited < timeoutMs; waited += pollMs) {
        const reading = value();

        if (reading !== undefined) {
          return reading;
        }

        sleep(pollMs);
      }

      return value();
    },
  };
};
