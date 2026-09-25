# The shard sets the flag on a success and reveals on a failed roll, so a flip is a roll the
# journal did not name
def flag_outcome(hidden_before, hidden_after):
    if not hidden_before and hidden_after:
        return "hidden"

    if hidden_before and not hidden_after:
        return "failed"

    return None


# Only a success opens the lore gump, so a gump that was not up before the use is one
def gump_outcome(gump_before, gump_after):
    return "read" if gump_after and gump_after != gump_before else None
