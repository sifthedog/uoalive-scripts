// player.maxMana reads 0 when the client has not been told it - the typings say so in as many words
// for maxHits, and the two arrive the same way - and 0 is the one value every comparison against a
// maximum reads as a catastrophe: a mana ceiling of 0 makes "wait until the pool is full" true the
// instant it is asked, so a trainer built on it meditates for no time at all and then casts with no
// mana, forever. It is the fault src/lib/weight.ts exists for on weightMax, on the stat that had no
// reader until something needed to wait for it.
export const manaCeiling = (): number | undefined => (player.maxMana > 0 ? player.maxMana : undefined);
