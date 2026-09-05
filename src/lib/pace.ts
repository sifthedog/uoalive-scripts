// The shard's own skill timer, learned rather than configured. Nothing in the API reports it, and a
// loop that guesses it low re-arms the very timer it is waiting out - which is what turns a fixed
// sleep into a run of nothing but 'you must wait'.
export const createPace = (options: {
  floor: number;
  step: number;
  max: number;
  easeAfter: number;
}) => {
  let delay = options.floor;
  let landed = 0;

  return {
    delay: (): number => delay,

    refused: (): number => {
      landed = 0;
      delay = Math.min(delay + options.step, options.max);

      return delay;
    },

    landed: (): number => {
      if (++landed < options.easeAfter) {
        return delay;
      }

      landed = 0;
      delay = Math.max(options.floor, delay - options.step);

      return delay;
    },
  };
};
