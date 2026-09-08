import API

from uo.crafttool import CraftTool
from uo.text import word_in


def pole_in_hand(graphics, name_words, layers):
    for layer in layers:
        held = API.FindLayer(layer)

        if held is None:
            continue

        if held.Graphic in graphics or word_in(held.Name, name_words):
            return held.Serial

    return None


# The shard takes the pole from the pack as well, so nothing is equipped; a held one is preferred
# because it is the one you meant
def find_pole(graphics, name_words, layers, log):
    held = pole_in_hand(graphics, name_words, layers)

    if held is not None:
        return held

    return CraftTool("fishing pole", graphics, name_words, log).serial()
