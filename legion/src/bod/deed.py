import API


def strip_article(name, articles):
    for article in articles:
        if name.startswith(article):
            return name[len(article):]

    return name


def to_int(text):
    try:
        return int(text.strip())
    except ValueError:
        return None


def parse_deed(lines, config):
    text = config["text"]
    low = [line.strip().lower() for line in lines if line and line.strip()]
    total = None
    exceptional = False
    large = False
    material = config["plain"]
    items = []

    for line in low:
        if text["large"] in line:
            large = True
        elif line.startswith(text["amount"]):
            total = to_int(line[len(text["amount"]):])
        elif text["exceptional"] in line:
            exceptional = True
        elif text["material_before"] in line:
            after = line.split(text["material_before"], 1)[1]
            material = after.replace(text["material_after"], "").strip(" .")
        elif ":" in line:
            name, count = line.rsplit(":", 1)
            done = to_int(count)

            if done is not None:
                items.append((strip_article(name.strip(), config["articles"]), done))

    if total is None or len(items) == 0:
        return None, "could not read it - the tooltip says '%s'" % " | ".join(low)

    request = {
        "large": large or len(items) > 1,
        "entries": items,
        "total": total,
        "exceptional": exceptional,
        "material": material,
    }

    if not request["large"]:
        request["item"] = items[0][0]
        request["done"] = items[0][1]

    return request, None


# The first trade, in order, whose recipes make every item the deed asks for
def trade_of(request, trades):
    for name, trade in trades:
        if all(item in trade["recipes"] for item, _done in request["entries"]):
            return name

    return None


def entry_request(request, item, done):
    return {
        "large": False,
        "entries": [(item, done)],
        "item": item,
        "done": done,
        "total": request["total"],
        "exceptional": request["exceptional"],
        "material": request["material"],
    }


class Deed(object):
    def __init__(self, serial, config, log):
        self.serial = serial
        self._config = config
        self._log = log
        self.request = None
        self._said_behind = False

    def _lines(self):
        props = API.ItemNameAndProps(self.serial, True, self._config["opl_timeout"]) or ""

        return [line.strip() for line in props.splitlines() if line.strip()]

    def read(self):
        request, why = parse_deed(self._lines(), self._config)

        if request is not None:
            self.request = request

        return request, why

    def describe(self):
        request = self.request
        flags = "%s, %s" % (", exceptional" if request["exceptional"] else "",
                            request["material"] or "no material")

        if request["large"]:
            return "large deed x%d: %s%s" % (
                request["total"],
                ", ".join("%s (%d done)" % entry for entry in request["entries"]), flags)

        return "%s x%d, %d done%s" % (request["item"], request["total"], request["done"], flags)

    # Asked for once, then read as it stands: a wait per read would stretch the settle by its
    # timeout on every poll
    def _lines_now(self):
        props = API.ItemNameAndProps(self.serial, False) or ""

        return [line.strip() for line in props.splitlines() if line.strip()]

    # The pack proved the combine; the tooltip catches up later, or on some builds never
    def settle_after_combine(self, count):
        waited = 0.0
        API.RequestOPLData([self.serial])

        while not API.StopRequested:
            request, _why = parse_deed(self._lines_now(), self._config)

            if request is not None and request["done"] >= count:
                if request["done"] > count:
                    self._log("the deed says %d done, more than the %d counted - taking the deed's"
                              % (request["done"], count))

                self.request["done"] = request["done"]

                return request["done"]

            if waited >= self._config["reread_settle"]:
                break

            API.Pause(self._config["reread_poll"])
            waited += self._config["reread_poll"]

        if not self._said_behind:
            self._said_behind = True
            self._log("the deed's tooltip is behind the count - trusting the pack from here on")

        self.request["done"] = count

        return count
