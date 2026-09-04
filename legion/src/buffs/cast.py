import API

from uo.journal import read_outcome


def cast_once(entry, standing, buckets, timeout, wait_slice):
    up_before = standing(entry)

    # Re-issuing a buff that is already standing is the one thing this script exists not to do
    if up_before:
        return "alreadyUp"

    mana_before = API.Player.Mana

    # Cancelled only when there is one to cancel: an unconditional cancel just before an action left
    # the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()
    API.CastSpell(entry["spell"])

    hit = read_outcome(buckets, timeout, wait_slice)

    if hit is not None:
        return hit

    # The proofs that do not go through the journal. A transition, not a state: one already standing
    # proves nothing, which is why up_before was read first.
    if standing(entry):
        return "cast"

    if API.Player.Mana < mana_before:
        return "cast"

    return None
