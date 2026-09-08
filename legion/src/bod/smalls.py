import API

from bod.deed import parse_deed
from uo.pack import pack_contents
from uo.text import any_in


def is_deed(item, config):
    return item.Graphic in config["deed_graphics"] or any_in(item.Name, config["deed_words"])


def matches(small, large):
    return (not small["large"]
            and small["item"] in [item for item, _done in large["entries"]]
            and small["total"] == large["total"]
            and small["exceptional"] == large["exceptional"]
            and small["material"] == large["material"])


# The small deeds in the pack that belong to the large one, the fuller of two for one item
def find_small_deeds(large, large_serial, config):
    found = {}

    for item in pack_contents():
        if item.Serial == large_serial or not is_deed(item, config):
            continue

        props = API.ItemNameAndProps(item.Serial, True, config["opl_timeout"]) or ""
        small, _why = parse_deed(props.splitlines(), config)

        if small is None or not matches(small, large):
            continue

        known = found.get(small["item"])

        if known is None or small["done"] > known["done"]:
            found[small["item"]] = {"serial": item.Serial, "done": small["done"]}

    return found
