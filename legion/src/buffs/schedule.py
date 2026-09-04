from uo.clock import now


def make_table(keep):
    return [{"entry": entry, "name": entry["spell"], "misses": 0, "until": 0.0, "retired": None}
            for entry in keep]


def due(item):
    return item["retired"] is None and now() >= item["until"]


def set_aside(item, for_seconds):
    item["misses"] = 0
    item["until"] = now() + for_seconds


def retire(item, why):
    item["retired"] = why


# The run has nothing left to do: every entry refused for a reason no later pass can change
def spent(table):
    return all(item["retired"] is not None for item in table)


# What a KEEP_UP=False run waits for. A retired entry counts as settled or it would never finish.
def settled(table, standing):
    return all(item["retired"] is not None or standing(item["entry"]) for item in table)
