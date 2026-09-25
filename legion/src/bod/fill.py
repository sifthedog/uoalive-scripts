import API

from bod.checks import stock_report
from uo.loop import backoff_for
from uo.menu import context_menu


class SmallFill(object):
    """The cycle loop for one small deed: combine what qualifies, else craft, until full."""

    def __init__(self, deed, items, crafter, picker, combiner, config, log, watch):
        self._deed = deed
        self._request = deed.request
        self._items = items
        self._crafter = crafter
        self._picker = picker
        self._combiner = combiner
        self._config = config
        self._log = log
        self._heartbeat = watch["heartbeat"]
        self._stall = watch["stall"]
        self._saves = watch["saves"]
        self._stop_reason = watch["stop_reason"]
        self._regain_mana = watch["regain_mana"]

        self.done = self._request["done"]
        self.combined = 0
        self.made = 0
        self.fails = 0
        self._unknown = 0
        self._throttled = 0
        self._no_tool = 0
        self._no_cursor = 0
        self._unwanted = 0
        self._dry = 0
        self._made_name = None
        self._cycle = 0
        self._said_throttle = False

    def owed(self):
        return self._request["total"] - self.done

    def summary(self):
        return "%d combined, %d made, %d failed, %d/%d in the deed" % (
            self.combined, self.made, self.fails, self.done, self._request["total"])

    def _end_cycle(self, phase):
        self._stall.end_cycle(phase, self._cycle, self.combined)

        return self._stall.reason()

    def _combine_now(self, offered):
        outcome, taken = self._combiner.combine(self._config["combine_target"], offered)

        if len(taken) > 0:
            self.combined += len(taken)
            self._no_cursor = 0
            self._items.forget_missing()
            self.done = self._deed.settle_after_combine(self.done + len(taken))
            self._stall.progressed()
            self._log("combined %d (%d/%d)" % (len(taken), self.done, self._request["total"]))
        elif outcome == "full":
            return "the deed is full"
        elif outcome in ("notRequested", "notExceptional", "wrongMaterial", "tooMany"):
            # Which of the offered pieces the shard meant is not said, so none is offered again
            self._items.reject(*offered)
            self._stall.progressed()
            self._log("the deed took none of the %d offered (%s), leaving them in the bag"
                      % (len(offered), outcome))

            if outcome == "wrongMaterial":
                self._picker.forget()
        elif outcome == "notInPack":
            return "the shard says the pieces are not in your pack"
        elif outcome in ("noCursor", "noGump"):
            self._no_cursor += 1

            if self._no_cursor >= self._config["max_no_cursor"]:
                return ("the deed's gump raised no cursor %d times - check BOD_COMBINE_BUTTON"
                        % self._config["max_no_cursor"])

            API.Pause(backoff_for(self._no_cursor, self._config["backoff"],
                                  self._config["backoff_max"]))
        else:
            self._unknown += 1
            self._log("unreadable combine outcome (%d/%d), check COMBINE_TEXT"
                      % (self._unknown, self._config["max_unknown"]))

        return None

    def salvage(self):
        bag = self._config["bag"]

        if not self._config["salvage"] or bag is None or len(self._items.leftovers()) == 0:
            return

        before = len(API.ItemsInContainer(bag, True) or [])

        if not context_menu(bag, self._config["salvage_entries"], self._config["context_timeout"]):
            self._log("the bag's menu has no %s entry - salvage it yourself"
                      % " / ".join(self._config["salvage_entries"]))

            return

        API.Pause(self._config["salvage_settle"])
        self._items.forget_missing()
        after = len(API.ItemsInContainer(bag, True) or [])
        self._log("salvaged: the bag went from %d items to %d, %s in the pack"
                  % (before, after, stock_report(self._config["stock"])))

    # A batch of pieces that are not even the deed's item is a wording mismatch: the row pressed
    # and the deed name different things. Another batch of them would only fill the pack
    def _judge_batch(self, before):
        self._items.prime()
        fresh = self._items.new_since(before)
        mine = [piece for piece in fresh if self._items.is_product(piece.Serial)]

        if len(fresh) > 0 and len(mine) == 0:
            self._unwanted += 1
            self._made_name = self._items.name_of(fresh[0].Serial)
        else:
            self._unwanted = 0

    def _craft(self):
        item = self._request["item"]
        material = self._request["material"]

        mana = self._config["mana"]

        if mana is not None and not self._regain_mana(mana.get(item, 0)):
            return "noMana"

        batch = self.owed()
        before = self._items.serials()
        outcome, made, failed = self._crafter.craft_batch(item, material, batch)
        self.made += made
        self.fails += failed

        if made > 0:
            self._judge_batch(before)

        if made + failed > 0:
            self._dry = 0
            self._log("batch of %d: %d made, %d failed%s"
                      % (batch, made, failed, "" if outcome == "made" else " (%s)" % outcome))
            self._stall.progressed()

        return "batch" if outcome == "made" else outcome

    def _after_craft(self, outcome, waiting):
        config = self._config
        item = self._request["item"]

        if self._unwanted >= config["max_unwanted"]:
            return ("the batch made '%s', and the deed asks for '%s' - the row pressed makes "
                    "something the deed will never take" % (self._made_name, item))

        if outcome != "throttled":
            self._throttled = 0

        if outcome is not None:
            self._unknown = 0

        if outcome in ("batch", "saving"):
            self._stall.progressed()
        elif outcome == "noMaterial":
            # What is already made goes in before the run ends
            if len(waiting) > 0:
                self._combine_now(waiting)

            return ("the shard says the materials ran out - %s in the pack, %d still owed"
                    % (stock_report(config["stock"]), self.owed()))
        elif outcome == "keg":
            return "a potion keg in the pack is swallowing the crafts - take it out and run again"
        elif outcome == "noMana":
            self._dry += 1

            if self._dry >= config["max_dry"]:
                return ("mana is not coming back - %d/%d, and one %s takes %d"
                        % (API.Player.Mana, API.Player.ManaMax, item, config["mana"].get(item, 0)))

            self._stall.progressed()
            self._log("short of mana (%d/%d), meditating before the next batch"
                      % (self._dry, config["max_dry"]))
        elif outcome == "toolWorn":
            self._stall.progressed()
            self._log("the tool wore out, looking for another")
        elif outcome == "skillTooLow":
            return "the shard says you cannot make a %s" % item
        elif outcome == "noAnvil":
            return "stand next to an anvil and a forge"
        elif outcome == "packFull":
            return "your backpack will not hold anything else - empty it and run again"
        elif outcome == "noRow":
            return "'%s' is not in the %s recipes" % (item, config["trade"])
        elif outcome == "noMaterialRow":
            return "the material page has no row for %s" % self._request["material"]
        elif outcome in ("noTool", "noGump"):
            self._no_tool += 1

            if self._no_tool >= config["max_no_tool"]:
                return ("no %s left" % config["tool_noun"] if outcome == "noTool"
                        else "the craft menu will not open")

            self._log("%s (%d/%d), trying again"
                      % ("no %s in the pack" % config["tool_noun"] if outcome == "noTool"
                         else "the tool opened no craft menu", self._no_tool, config["max_no_tool"]))
            API.Pause(backoff_for(self._no_tool, config["backoff"], config["backoff_max"]))
        elif outcome == "throttled":
            self._throttled += 1

            if self._throttled >= config["max_throttled"]:
                return "%d throttled crafts in a row" % config["max_throttled"]

            waiting = backoff_for(self._throttled, config["backoff"], config["backoff_max"])

            if not self._said_throttle:
                self._said_throttle = True
                self._log("the shard is pacing the crafts - waiting %.1fs" % waiting)

            API.Pause(waiting)
        else:
            self._unknown += 1
            self._log("unreadable outcome (%d/%d), check the %s outcome text"
                      % (self._unknown, config["max_unknown"], config["trade"]))

        if outcome not in ("noTool", "noGump"):
            self._no_tool = 0

        return None

    # None when the deed is full, otherwise why it stopped
    def run(self):
        config = self._config
        stop = None

        while stop is None and self._cycle < config["max_cycles"]:
            self._cycle += 1
            stop = self._stop_reason()

            if stop is not None:
                break

            if self._saves.is_saving():
                self._saves.wait_out()
                self._unknown = 0
                self._throttled = 0
                self._stall.progressed()
                stop = self._end_cycle("saving")
                continue

            if self.owed() <= 0:
                break

            waiting = self._items.qualifying()

            if len(waiting) > 0:
                stop = self._combine_now(waiting)

                if stop == "the deed is full":
                    stop = None
                    self.done = self._request["total"]
                    break

                if stop is None and self._unknown >= config["max_unknown"]:
                    stop = "%d unreadable outcomes in a row" % config["max_unknown"]

                if stop is None:
                    self.salvage()
                    stop = self._end_cycle("combining")
                    API.Pause(config["step_delay"])

                continue

            outcome = self._craft()
            stop = self._after_craft(outcome, waiting)

            if stop is None and self._unknown >= config["max_unknown"]:
                stop = "%d unreadable outcomes in a row" % config["max_unknown"]

            if stop is None:
                stop = self._end_cycle(outcome if outcome is not None else "unknown")
                API.Pause(config["step_delay"])

        if stop is None and self.owed() > 0:
            stop = "hit the %d cycle backstop" % config["max_cycles"]

        if self.owed() <= 0:
            self.salvage()

        return stop
