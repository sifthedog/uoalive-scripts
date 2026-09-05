// 'noEntry' is the shard offering a menu without the entry on it, which is a different fact from a
// menu that never arrived: the first says what this object is, the second says nothing at all.
export type MenuChoice = 'pressed' | 'noEntry' | 'noMenu';

// The context menu is the only way to reach what the client API has no call for - renaming a pet,
// releasing one - and its entries are numbered by the server, so a menu that omits one leaves a gap.
export const chooseMenuEntry = (options: {
  serial: number;
  texts: string[];
  timeoutMs: number;
}): MenuChoice => {
  // A menu left open from the last object answers for that object, not this one
  popupMenu.close();

  popupMenu.request(options.serial, options.timeoutMs);

  const content = popupMenu.waitForContent(options.timeoutMs);

  if (!content || content.serial !== options.serial) {
    popupMenu.close();

    return 'noMenu';
  }

  const wanted = options.texts.map((text) => text.toLowerCase());

  const entry = content.items.find((item) =>
    wanted.some((text) => item.text.toLowerCase().includes(text)),
  );

  if (!entry) {
    popupMenu.close();

    return 'noEntry';
  }

  popupMenu.reply(entry.index);

  return 'pressed';
};
