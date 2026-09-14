import API

from bod.deed import to_int
from uo.pack import amount_of, hue_of, pack_contents
from uo.text import word_in, words_of


def is_ingot(item, config):
    return item.Graphic in config["ingot_graphics"] or word_in(item.Name, config["ingot_words"])


# The name is where the shard writes the metal ('Valorite Ingots'); plain ingots carry none and
# fall through to the hue
def material_of(item, config):
    words = words_of(item.Name)

    for material in config["materials"]:
        wanted = words_of(material)

        if words[:len(wanted)] == wanted:
            return material

    hue = hue_of(item)

    return config["hues"].get(hue, "hue 0x%x" % hue)


def kind_of(item, kinds):
    for name in kinds:
        if item.Graphic in kinds[name]:
            return name

    return None


# Ingots by the material they are ('iron ingots'), and every other stock kind by its art
def stock_counts(config):
    counts = {}
    kinds = config.get("kinds", {})

    for item in pack_contents():
        if is_ingot(item, config):
            name = "%s ingots" % material_of(item, config)
        else:
            name = kind_of(item, kinds)

        if name is not None:
            counts[name] = counts.get(name, 0) + amount_of(item)

    return counts


def stock_report(config):
    counts = stock_counts(config)

    if len(counts) == 0:
        return "no stock"

    return ", ".join("%d %s" % (counts[name], name) for name in sorted(counts))


def uses_of(props, config):
    for line in (props or "").splitlines():
        low = line.strip().lower()

        if config["uses_text"] in low and ":" in low:
            return to_int(low.rsplit(":", 1)[1])

    return None


# Every tool's charges added up, and how many tools said nothing
def tool_uses(serials, config):
    total = 0
    unread = 0

    for serial in serials:
        uses = uses_of(API.ItemNameAndProps(serial, True, config["opl_timeout"]), config)

        if uses is None:
            unread += 1
        else:
            total += uses

    return total, unread


# A cost is ingots of the deed's material when it is a number, and stock per kind when it is a dict
def needs_of(request, cost):
    if isinstance(cost, dict):
        return dict(cost)

    return {"%s ingots" % request["material"]: cost}


# Problems stop the run; notes are said and the run goes on. Requests are summed: a large deed
# is checked as every small it still needs
def preflight(requests, tool_serials, config):
    problems = []
    notes = []
    owed = 0
    unknown = []
    needed = {}
    exceptional = False

    for request in requests:
        pieces = request["total"] - request["done"]
        owed += pieces
        exceptional = exceptional or request["exceptional"]
        cost = config["costs"].get(request["item"])

        if cost is None:
            unknown.append(request["item"])
        else:
            for name, each in needs_of(request, cost).items():
                needed[name] = needed.get(name, 0) + each * pieces

    if len(unknown) > 0:
        notes.append("no cost is known for %s, so those are not checked"
                     % ", ".join("'%s'" % item for item in unknown))

    held = stock_counts(config)

    for name in sorted(needed):
        have = held.get(name, 0)

        if have < needed[name]:
            problems.append("%d %s for the %d pieces owed, and the pack holds %d"
                            % (needed[name], name, owed, have))
        else:
            notes.append("%d %s cover the %d pieces owed, %d in the pack"
                         % (needed[name], name, owed, have))

    uses, unread = tool_uses(tool_serials, config)

    if unread == len(tool_serials):
        notes.append("no tool reports its uses remaining, so the charges are not checked")
    elif uses < owed:
        problems.append("%d uses left across %d tool(s) for %d pieces owed"
                        % (uses, len(tool_serials), owed))
    else:
        notes.append("%d uses left across %d tool(s) for %d pieces owed"
                     % (uses, len(tool_serials), owed))

    if exceptional and len(problems) == 0:
        notes.append("an exceptional deed takes more crafts than pieces - the counts above cover "
                     "the pieces only")

    return problems, notes
