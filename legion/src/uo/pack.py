import API


# API.Stop() only lands at the next Pause, and every client call before it answers nothing - so the
# backpack reads as null for the rest of a stopping script, and ItemsInContainer throws on a null
# container rather than answering none. Every caller here wants "nothing in the pack" for that
def _contents(recursive):
    backpack = API.Backpack

    if not backpack:
        return []

    items = API.ItemsInContainer(backpack, recursive)

    return items if items else []


def pack_contents():
    return _contents(True)


# The item cap is per container, so the guard and the combine both count the top level only
def pack_top_level():
    return _contents(False)


# None is an unreported stack, not an empty one: counted as 0 it would hide the ore a swing just
# delivered, which is the proof that the swing landed
def amount_of(item):
    amount = getattr(item, "Amount", None)

    return amount if amount is not None else 1


def hue_of(item):
    return getattr(item, "Hue", 0) or 0


def counts_by_graphic(items):
    counts = {}

    for item in items:
        key = (item.Graphic, hue_of(item))
        counts[key] = counts.get(key, 0) + amount_of(item)

    return counts


def diff_counts(before, after):
    gained = {}
    lost = {}

    for key in set(list(before.keys()) + list(after.keys())):
        change = after.get(key, 0) - before.get(key, 0)

        if change > 0:
            gained[key] = change
        elif change < 0:
            lost[key] = -change

    return gained, lost


def count_of(graphics):
    return sum(amount_of(item) for item in pack_contents() if item.Graphic in graphics)


def items_of(keys):
    return [item for item in pack_contents() if (item.Graphic, hue_of(item)) in keys]
