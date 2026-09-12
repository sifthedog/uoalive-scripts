import API

from uo.entity import player
from uo.pack import pack_top_level
from uo.weight import over_buffer


def first_reason(clauses):
    for clause in clauses:
        reason = clause()

        if reason is not None:
            return reason

    return None


def stopped(text):
    def clause():
        return text if API.StopRequested else None

    return clause


def dead():
    def clause():
        me = player()

        return "you are dead" if me is not None and me.IsDead else None

    return clause


def pack_full(limit):
    def clause():
        return "the pack is at its item cap" if len(pack_top_level()) >= limit else None

    return clause


def overweight(buffer):
    def clause():
        me = player()

        if me is None or not over_buffer(buffer):
            return None

        return "overweight at %d/%d" % (me.Weight, me.WeightMax)

    return clause


# By the value as well as the base: with no base reported, or a lifted value, the run never ends
def skill_capped(name):
    def clause():
        skill = API.GetSkill(name) if name is not None else None

        if skill is None:
            return None

        base = getattr(skill, "Base", None) or 0.0
        value = skill.Value

        if max(base, value) <= 0 or max(base, value) < skill.Cap:
            return None

        if base >= skill.Cap:
            return "%s is capped at %.1f" % (name, base)

        if base > 0:
            return ("%s shows %.1f against its %.1f cap while its base is %.1f - take off what lifts "
                    "it to keep gaining" % (name, value, skill.Cap, base))

        return "%s is capped at %.1f" % (name, value)

    return clause


def hurt(floor):
    def clause():
        me = player()

        if me is None:
            return None

        # HitsMax reads 0 before the client has been told, the way ManaMax does
        ceiling = me.HitsMax

        if ceiling > 0 and me.Hits < ceiling * floor:
            return "hurt (%d/%d)" % (me.Hits, ceiling)

        return None

    return clause


def no_follower_slots():
    def clause():
        me = player()

        if me is None:
            return None

        slots = me.FollowersMax

        # Keeping the tames fills the slots, and a shard with no room left refuses every attempt
        # without saying why
        if slots > 0 and me.Followers >= slots:
            return "no follower slots left"

        return None

    return clause
