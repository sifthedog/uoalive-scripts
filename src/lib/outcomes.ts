// A shard words its results in prose, so every action loop reads the journal against a table of
// phrases and maps whichever one landed back to the bucket it came from. The phrases are guesses
// until a live run confirms them, which is why a miss shows up as an 'unknown' outcome that stops
// the run rather than as a silent wrong turn.

export interface Vocabulary<T extends Record<string, string[]>> {
  // Everything to wait for in one array, which is what journal.waitForTextAny takes
  all: string[];

  // Reverse lookup: the first bucket whose phrases include the match. Bucket order therefore
  // decides between two phrases close enough to both match, which is worth knowing when adding one.
  outcomeFor: (matched: string) => keyof T | undefined;
}

export const outcomeVocabulary = <T extends Record<string, string[]>>(text: T): Vocabulary<T> => ({
  all: Object.values(text).flat(),
  outcomeFor: (matched) => (Object.keys(text) as (keyof T)[]).find((name) => text[name].includes(matched)),
});
