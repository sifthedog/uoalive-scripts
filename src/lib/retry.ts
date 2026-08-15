// An equip, a dismount and anything else the shard does asynchronously: the call returns before the
// world has changed. Poll for the proof, and reissue rather than give up on the first attempt - a
// throttled action looks exactly like one that never arrived.
export const untilLanded = (options: {
  label: string;
  attempts: number;
  timeoutMs: number;
  pollMs: number;
  act: () => void;
  landed: () => boolean;
}): boolean => {
  for (let attempt = 1; attempt <= options.attempts; attempt++) {
    options.act();

    for (let waited = 0; waited < options.timeoutMs; waited += options.pollMs) {
      sleep(options.pollMs);

      if (options.landed()) {
        return true;
      }
    }

    log(`${options.label}: attempt ${attempt} did not land, reissuing`);
  }

  log(`${options.label}: gave up`);
  return false;
};
