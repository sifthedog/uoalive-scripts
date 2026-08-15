// player.maxMana reads 0 when the client has not been told it, and 0 makes "wait until the pool is
// full" true the instant it is asked - so a trainer built on it meditates for no time at all and
// then casts with no mana, forever.
export const manaCeiling = (): number | undefined => (player.maxMana > 0 ? player.maxMana : undefined);

// The same fault on maxHits, which the typings name outright. Undefined is the only honest answer
// while the client is refreshing stats: a health floor read against a maximum of 0 either never
// fires or fires on cycle zero, depending on which way it is written.
export const hitsCeiling = (): number | undefined => (player.maxHits > 0 ? player.maxHits : undefined);
