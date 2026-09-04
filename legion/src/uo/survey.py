from uo.entity import hex_of


# The dead-end report: what the run actually saw, so a wrong art table can be corrected from it
def survey(tiles, radius, limit, matches, log, extra_marks=None):
    seen = {}

    for tile in tiles:
        key = "%s:%d" % ("land" if tile["is_land"] else "static", tile["graphic"])
        entry = seen.get(key)

        if entry is None:
            seen[key] = [1, tile]
        else:
            entry[0] += 1

    ranked = sorted(seen.values(), key=lambda entry: entry[0], reverse=True)

    log("the arts within %d, commonest first:" % radius)

    for count, tile in ranked[:limit]:
        marks = []

        if matches(tile):
            marks.append("MATCHES")

        if not tile["is_land"]:
            marks.append("'%s'" % (tile["name"] or "?"))

        if extra_marks is not None:
            marks.extend(extra_marks(tile))

        # Decimal as well as hex: the RunUO tables the art sets are seeded from are decimal
        log("  %s %s (%d) x%d z%d %s"
            % ("land" if tile["is_land"] else "static", hex_of(tile["graphic"]), tile["graphic"],
               count, tile["z"], " ".join(marks)))
