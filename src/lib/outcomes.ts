// A shard words its results in prose, so every action loop reads the journal against a table of
// phrases and maps whichever one landed back to its bucket. The phrases are guesses until a live run
// confirms them, which is why a miss shows up as an 'unknown' outcome rather than a silent wrong turn.

export interface Vocabulary<T extends Record<string, string[] | undefined>> {
  // Everything to wait for in one array, which is what journal.waitForTextAny takes
  all: string[];

  // The first bucket whose phrases include the match, so bucket order decides between two phrases
  // close enough that both match.
  outcomeFor: (matched: string) => keyof T | undefined;
}

// A bucket may be absent rather than empty: where the buckets are a fixed set shared by more than one
// script, a folder leaves out what cannot happen to it.
export const outcomeVocabulary = <T extends Record<string, string[] | undefined>>(
  text: T,
): Vocabulary<T> => ({
  all: Object.values(text)
    .flat()
    .filter((phrase): phrase is string => phrase !== undefined),
  outcomeFor: (matched) =>
    (Object.keys(text) as (keyof T)[]).find((name) => text[name]?.includes(matched)),
});
