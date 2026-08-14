import { OPL_TIMEOUT, PEEK_CONTENTS } from './config.js';

// A container's tooltip carries what is in it - RunUO renders it as "Contents: 3/125, 4 stones" -
// so the count can be had without the double-click, the 800ms wait and the window. On a pile that
// is mostly already empty that is the difference between opening a hundred boxes and opening two.
//
// What it gives is a *count*, not a list: there is no way to know a box holds an iron key
// specifically without opening it. Zero is the useful answer, and zero is most of them.

let oplReportsContents = true;

// Same shape tool.ts reads "uses remaining" out of: the property text and its values, joined
const textOf = (property: { text?: string; values?: { text?: string }[] }): string => {
  const values = (property.values ?? []).map((value) => value.text).join(' ');
  return `${property.text ?? ''} ${values}`;
};

// undefined means "no idea, open it and see" - never "empty", because guessing empty on a box that
// is not would hand a key to a vendor
export const peekContents = (serial: number): number | undefined => {
  if (!PEEK_CONTENTS || !oplReportsContents) {
    return undefined;
  }

  const opl = client.queryItemOPL(serial, OPL_TIMEOUT);

  for (const property of opl?.properties ?? []) {
    const match = textOf(property).match(/contents[^0-9]*([0-9]+)/i);

    if (match) {
      return Number(match[1]);
    }
  }

  // The shard does not send it. Asked once and then left alone, the way tool.ts stops asking for
  // "uses remaining" - otherwise every box pays the OPL timeout for an answer that never comes.
  oplReportsContents = false;
  log('boxes: no "contents" line in the tooltips here, so every box has to be opened to be checked');

  return undefined;
};
