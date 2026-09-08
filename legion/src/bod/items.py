import API

from bod.deed import strip_article
from uo.pack import amount_of, pack_contents
from uo.text import word_in, words_of


class ItemBook(object):
    """What the tooltip says each pack item is, and whether the deed would take it."""

    def __init__(self, request, config, log):
        self._request = request
        self._config = config
        self._log = log
        self._verdicts = {}
        self._asked = {}
        self._rejected = set()

    def _material_names(self):
        material = self._request["material"]

        return [material] + list(self._config["aliases"].get(material, []))

    def _plain(self):
        return self._request["material"] == self._config["plain"]

    # Stock folds the material into the name: 'dull copper platemail gorget'
    def _product_names(self):
        item = self._request["item"]
        names = [item]

        if not self._plain():
            names.extend("%s %s" % (name, item) for name in self._material_names())

        return names

    def _judge(self, lines):
        name = strip_article(lines[0].lower(), self._config["articles"])

        body = [line.lower() for line in lines[1:]]
        product = name in self._product_names()
        exceptional = word_in(" ".join(body), [self._config["exceptional_text"]])

        if self._plain():
            material = True
        else:
            wanted = [words_of(alias) for alias in self._material_names()]
            material = (name != self._request["item"]
                        or len([line for line in body if words_of(line) in wanted]) > 0)

        return {
            "product": product,
            "qualifies": product and material and (exceptional or not self._request["exceptional"]),
        }

    def look(self, serial):
        if serial in self._verdicts:
            return self._verdicts[serial]

        if self._asked.get(serial, 0) >= self._config["asks"]:
            return None

        self._asked[serial] = self._asked.get(serial, 0) + 1
        props = API.ItemNameAndProps(serial, True, self._config["opl_timeout"]) or ""
        lines = [line.strip() for line in props.splitlines() if line.strip()]

        if len(lines) == 0:
            return None

        self._verdicts[serial] = self._judge(lines)
        self._verdicts[serial]["name"] = lines[0]

        return self._verdicts[serial]

    def name_of(self, serial):
        verdict = self.look(serial)

        return "(no tooltip)" if verdict is None else verdict["name"]

    def is_product(self, serial):
        verdict = self.look(serial)

        return None if verdict is None else verdict["product"]

    def reject(self, *serials):
        self._rejected.update(serials)

    # Stacks and bags are never the product, and each tooltip read is a wait
    def _candidates(self):
        return [item for item in pack_contents()
                if amount_of(item) == 1 and not getattr(item, "IsContainer", False)]

    def serials(self):
        return set(item.Serial for item in pack_contents())

    def new_since(self, before):
        return [item for item in self._candidates() if item.Serial not in before]

    # One request for every unread piece, so the reads below do not each wait their turn
    def prime(self):
        unread = [item.Serial for item in self._candidates()
                  if item.Serial not in self._verdicts and item.Serial not in self._rejected
                  and self._asked.get(item.Serial, 0) < self._config["asks"]]

        if len(unread) == 0:
            return

        API.RequestOPLData(unread)
        API.Pause(self._config["opl_settle"])

    def qualifying(self):
        self.prime()
        found = []

        for item in self._candidates():
            if item.Serial in self._rejected:
                continue

            verdict = self.look(item.Serial)

            if verdict is not None and verdict["qualifies"]:
                found.append(item.Serial)

        return found

    # What a salvage would take: judged pieces the deed did not, or would not
    def leftovers(self):
        return [item.Serial for item in self._candidates()
                if item.Serial in self._verdicts
                and (item.Serial in self._rejected or not self._verdicts[item.Serial]["qualifies"])]

    # The shard reissues the serial of an item the deed took
    def forget_missing(self):
        here = self.serials()

        for serial in list(self._verdicts.keys()):
            if serial not in here:
                del self._verdicts[serial]
                self._asked.pop(serial, None)
