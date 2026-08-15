import { SELL_AT, SELL_AT_SLOTS } from './config.js';

// Why a sale is due, or undefined to carry on watching. Split out from the loop so the policy can
// be tested without a client: what surrounds it is all sleeps, globals and speech.
//
// The string is the reason, and it is what the run says out loud - so it names the number that
// tripped rather than merely reporting that something did.
export const reasonToSell = (held: number, slots: number): string | undefined => {
  if (held >= SELL_AT) {
    return `${held} held`;
  }

  // A full pack is a reason to sell only if selling would do something about it. With none of the
  // watched item in there the sale can free nothing, and firing anyway would say 'vendor sell'
  // every poll for as long as the pack stayed full - of items this script was never watching.
  if (slots >= SELL_AT_SLOTS && held > 0) {
    return `${slots} pack slots used`;
  }

  return undefined;
};
