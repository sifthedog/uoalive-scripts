// The one clock in the scripts, so tests have one thing to fake and every cooldown, heartbeat and
// sliced sleep is measured against the same reading.
export const now = (): number => Date.now();
