# The shard sets the flag on a success and reveals on a failed roll, so a flip is a roll the
# journal did not name
def flag_outcome(hidden_before, hidden_after):
    if not hidden_before and hidden_after:
        return "hidden"

    if hidden_before and not hidden_after:
        return "failed"

    return None
