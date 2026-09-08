def make_plan(stages):
    return sorted(stages, key=lambda stage: stage["up_to"])


def goal_of(plan):
    return max([stage["up_to"] for stage in plan]) if plan else 0.0


# The same table that picks the spell answers whether there is one left, so the two cannot disagree
def stage_now(plan, value):
    for stage in plan:
        if value < stage["up_to"]:
            return stage

    return None


def describe_plan(plan):
    return ", ".join("%s to %.1f" % (stage["spell"], stage["up_to"]) for stage in plan)


# What one casting cycle of a row costs in wall clock, and the denominator a dry mana stretch is
# priced against
def cycle_cost(stage, fallback_timeout, fallback_delay):
    return max(0.1, stage.get("cast_timeout", fallback_timeout)
               + stage.get("cast_delay", fallback_delay))


# Ceilings are exclusive; None catches everything above the last one
def band_for(bands, value):
    if value is None:
        return None

    for ceiling, product in bands:
        if ceiling is None or value < ceiling:
            return product

    return None
