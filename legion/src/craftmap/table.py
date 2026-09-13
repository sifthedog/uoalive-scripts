# The block a craft script's config.py pastes in: the shard's group names, then every row under
# its group, keyed the way Crafter looks a product up
def recipes_block(title, stamp, categories, rows):
    lines = ["# %s, read off the menu on %s" % (title, stamp), "CATEGORY_NAMES = ["]

    for label, _button in categories:
        lines.append('    "%s",' % label.lower())

    lines += ["]", "", "RECIPES = {"]
    seen = set()

    for label, category in categories:
        lines.append("    # %s (button %d)" % (label, category))

        for name, button in rows.get(category, []):
            key = name.lower()
            entry = '"%s": (%d, %d),' % (key, category, button)

            # The menu lists an item twice (bulletin board, east and south); the first is the table's
            if key in seen:
                lines.append("    # %s  listed again, the first kept" % entry)
            else:
                seen.add(key)
                lines.append("    " + entry)

    lines.append("}")

    return "\n".join(lines) + "\n"
