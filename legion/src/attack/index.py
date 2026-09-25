import API

from attack.config import OPL_TIMEOUT, OWNED_PROP_WORDS, RANGE
from attack.foe import label, nearest_foe
from uo.entity import hex_of
from uo.guards import dead, first_reason
from uo.log import make_log

log = make_log("attack")


def attack():
    if API.HasTarget():
        API.CancelTarget()

    reason = first_reason([dead()])

    if reason is not None:
        return reason

    foe, props = nearest_foe(RANGE, OWNED_PROP_WORDS, OPL_TIMEOUT)

    if foe is None:
        return "nothing hostile within %d tiles" % RANGE

    API.SetWarMode(True)
    API.Attack(foe.Serial)

    ending = "attacking '%s' %s %d tiles off" % (label(foe, props), hex_of(foe.Graphic), foe.Distance)

    return ending if props else ending + " - tooltip never came"


try:
    ending = attack()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    ending = "threw - %s" % error

log(ending)
API.Stop()
