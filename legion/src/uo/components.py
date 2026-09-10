def short_of(needs, counts):
    short = {}

    for kind in needs:
        missing = needs[kind] - counts.get(kind, 0)

        if missing > 0:
            short[kind] = missing

    return short


def affordable(needs, counts):
    crafts = None

    for kind in needs:
        if needs[kind] <= 0:
            continue

        can = counts.get(kind, 0) // needs[kind]
        crafts = can if crafts is None else min(crafts, can)

    return 0 if crafts is None else crafts


# In the caller's kind order, so the line reads the same each time
def shortfall_report(short, order):
    parts = ["%d %s" % (short[kind], kind) for kind in order if kind in short]
    parts += ["%d %s" % (short[kind], kind) for kind in sorted(short) if kind not in order]

    return ", ".join(parts)
