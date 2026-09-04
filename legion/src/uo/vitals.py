from uo.entity import player


def weight_reading():
    me = player()

    return "?/?" if me is None else "%d/%d" % (me.Weight, me.WeightMax)


def mana_reading():
    me = player()

    return "?/?" if me is None else "%d/%d mana" % (me.Mana, me.ManaMax)


def where():
    me = player()

    return "somewhere" if me is None else "at %d,%d" % (me.X, me.Y)


def position_and_weight():
    return "%s, %s" % (where(), weight_reading())


def position_and_mana():
    return "%s, %s" % (where(), mana_reading())
