import API

from uo.entity import hex_of, player
from uo.menu import context_menu
from uo.retry import settled
from uo.text import any_in, clipped


def tooltip_of(mobile):
    try:
        return mobile.NameAndProps(False) or ""
    except Exception:
        return ""


class Vendor(object):
    def __init__(self, wood, menu, config, log, heartbeat, products_in_pack):
        self._wood = wood
        self._menu = menu
        self._config = config
        self._log = log
        self._heartbeat = heartbeat
        self._products_in_pack = products_in_pack
        self._said_no_vendor = False
        self._said_sell_how = False

    def _candidates(self):
        me = player()
        mine = me.Serial if me is not None else None
        found = []

        for mobile in API.GetAllMobiles(None, self._config["scan_radius"]) or []:
            # Your own pets are the bulk of what stands around a crafter, and only yours rename
            if mobile.IsDead or mobile.Serial == mine or mobile.IsRenamable:
                continue

            found.append(mobile)

        return found

    # Name first because it costs nothing, tooltips second because they cost a round trip each: a
    # shopkeeper is "Alger" by name and "the bowyer" only in the tooltip, which is why the name pass
    # alone kept answering that there was no bowyer in sight.
    def _find(self):
        if self._config["serial"]:
            return API.FindMobile(self._config["serial"])

        candidates = self._candidates()

        for mobile in candidates:
            if any_in(mobile.Name, self._config["titles"]):
                return mobile

        if len(candidates) == 0:
            return None

        API.RequestOPLData([mobile.Serial for mobile in candidates])
        API.Pause(self._config["opl_wait"])

        for mobile in candidates:
            if any_in(tooltip_of(mobile), self._config["titles"]):
                return mobile

        return None

    # Re-resolved every pass rather than the found mobile trusted: a pathfind that ends early leaves
    # you short, and the only way to know is to ask where the vendor is now.
    def _walk_to(self, serial):
        within = self._config["range"]

        for _step in range(self._config["steps"]):
            here = API.FindMobile(serial)

            if here is None:
                return None

            if here.Distance <= within:
                return here

            API.PathfindEntity(serial, within, True, self._config["pathfind_timeout"], True)
            API.CancelPathfinding()
            API.Pause(self._config["step_delay"])

        here = API.FindMobile(serial)

        return here if here is not None and here.Distance <= within else None

    # The context menu first: it is the vendor's own 'Sell', matched by its text, and it does not
    # depend on the shard hearing a phrase. The phrase is still there for a menu with no such entry.
    def _ask_to_sell(self, serial):
        asked = context_menu(serial, [self._config["sell_entry"]],
                             self._config["context_timeout"])

        if not asked:
            API.Msg(self._config["sell_phrase"])

        if not self._said_sell_how:
            self._said_sell_how = True
            self._log("selling by %s" % ("the vendor's own Sell menu" if asked
                                         else "saying '%s'" % self._config["sell_phrase"]))

        return asked

    def sell_trip(self):
        vendor = self._find()

        if vendor is None:
            if not self._said_no_vendor:
                self._said_no_vendor = True
                names = [mobile.Name or "?" for mobile in self._candidates()]
                self._log("no bowyer within %d - looked at %d: %s"
                          % (self._config["scan_radius"], len(names),
                             clipped(", ".join(names), self._config["text_limit"]) or "nobody"))

            return False

        self._said_no_vendor = False

        name = vendor.Name or hex_of(vendor.Serial)
        here = self._walk_to(vendor.Serial)

        if here is None:
            self._log("could not get next to '%s', trying again next time" % name)

            return False

        before = self._products_in_pack()
        self._log("selling %d to '%s'" % (before, name))

        self._ask_to_sell(vendor.Serial)

        sold = settled(self._config["sell_timeout"], self._config["sell_poll"],
                       lambda: self._products_in_pack() < before)

        # Never the bare form: it closes the last gump, which is as likely to be the craft menu
        found = API.HasGump()

        if found and found != self._menu.current_id() and not self._menu.is_craft_gump(found):
            API.CloseGump(found)

        if not sold:
            self._log("the vendor bought nothing - is the auto-sell agent on?")
        else:
            self._log("sold, %d left in the pack" % self._products_in_pack())

        self._heartbeat.reset()

        return sold
