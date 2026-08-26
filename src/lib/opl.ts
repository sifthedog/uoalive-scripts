// The client throws out of queryItemOPL rather than answering emptily, the same way item.contents
// does - it took a sell-watch down mid-run, after the vendor had already paid for the goods.
// Latched whole rather than per serial, unlike contentsOf: a shard that will not answer for one
// item will not answer for the next, and the callers' own miss counts are what stop the asking.
let threw = false;

export const queryOPL = (
  serial: number,
  timeoutMs: number,
  prefix: string,
): ReturnType<typeof client.queryItemOPL> | undefined => {
  try {
    return client.queryItemOPL(serial, timeoutMs);
  } catch (error) {
    if (!threw) {
      threw = true;
      log(`${prefix}: the tooltip lookup would not answer - ${String(error)}`);
    }

    return undefined;
  }
};
