import API

from uo.entity import hex_of
from uo.journal import forget, said
from uo.pack import amount_of
from uo.weight import over_buffer


class Haul(object):
    """Getting the boards onto the pack animals, and knowing when they will take no more."""

    def __init__(self, wood, boards, saves, config, log):
        self._wood = wood
        self._boards = boards
        self._saves = saves
        self._config = config
        self._log = log

        # A list chosen rather than guessed - from config or from the cursor - is the law, so an
        # animal out of sight for a moment is not a reason to go loading a stranger's mule
        self._pinned = list(config["serials"])
        self._reported_animals = False
        self._reported_no_animal = False

        # Kept from the last search so the trouble watch can re-resolve one mobile rather than
        # paying a GetAllMobiles per body every cycle
        self._last_serial = None

        # Never cleared: what empties a pack horse is a trip to the bank, and that ends the run
        self._overloaded = set()
        self._opened = set()
        self._said_all_full = False
        self._hauling = True
        self._empty_hauls = 0

    def hauling(self):
        return self._hauling

    def pick(self):
        if API.Player.IsMounted:
            self._log("you are mounted - dismount first if the animal you want is the one you "
                      "are riding")

        self._log("target the pack animals to load, ESC when done")

        picked = []

        for _pick in range(self._config["max_picks"]):
            if API.HasTarget():
                API.CancelTarget()

            serial = API.RequestTarget(self._config["pick_timeout"])

            # Falsy is ESC or a cursor that timed out, and either one ends the selection
            if not serial:
                break

            animal = API.FindMobile(serial)

            # Not an ending: a misclick on the ground should cost the click and nothing more
            if animal is None:
                self._log("%s is not a mobile" % hex_of(serial))
                continue

            if serial in picked:
                continue

            # Not a refusal either: the graphics table is a guess at this shard, so a body it has
            # never heard of is worth reporting and then using
            if animal.Graphic not in self._config["graphics"]:
                self._log("%s is not a body PACK_ANIMAL_GRAPHICS knows, using it anyway"
                          % hex_of(animal.Graphic))

            picked.append(serial)
            self._log("picked '%s' %s" % (animal.Name or "?", hex_of(serial)))

        if API.HasTarget():
            API.CancelTarget()

        if len(picked) == 0:
            self._log("nothing picked, looking for the animals instead")

            return []

        self._pinned = picked

        return picked

    def find(self):
        found = []

        if len(self._pinned) > 0:
            # A pinned serial can be hand-written, so check what came back rather than trusting it
            for serial in self._pinned:
                animal = API.FindMobile(serial)

                if animal is not None and not animal.IsDead:
                    found.append(animal)
        else:
            for graphic in self._config["graphics"]:
                for animal in API.GetAllMobiles(graphic, self._config["radius"]) or []:
                    if not animal.IsDead:
                        found.append(animal)

            # Only your own pets can be renamed, so this is what tells yours from a stranger's
            mine = [animal for animal in found if animal.IsRenamable]

            if len(mine) > 0:
                found = mine

        if len(found) == 0:
            return []

        if not self._reported_animals:
            self._reported_animals = True
            names = ", ".join("'%s'" % (animal.Name or "?") for animal in found)
            self._log("%d pack animal(s) - %s" % (len(found), names))

        # Nearest first, so the closest one fills before you walk past it to another
        found.sort(key=lambda animal: animal.Distance)
        self._last_serial = found[0].Serial

        return found

    def companion(self):
        return API.FindMobile(self._last_serial) if self._last_serial is not None else None

    # A pet's coordinates go stale within a cycle, so the serial is re-resolved rather than the
    # find result trusted
    def _walk_to(self, serial):
        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance <= self._config["unload_range"]:
            return here

        API.PathfindEntity(serial, self._config["unload_range"], True,
                           self._config["pathfind_timeout"])
        API.CancelPathfinding()

        here = API.FindMobile(serial)

        if here is None:
            self._log("lost track of %s" % hex_of(serial))

            return None

        if here.Distance > self._config["unload_range"]:
            self._log("could not get within %d of '%s', it is %d tiles off"
                      % (self._config["unload_range"], here.Name or "?", here.Distance))

            return None

        return here

    # Two independent reads, and no double-click fallback: the web client had only the layer, and
    # its fallback is a UseObject on a rideable giant beetle, which mounts you. Nothing in this file
    # dismounts, so a mount here would cost the rest of the run.
    def _animal_pack(self, animal):
        pack = getattr(animal, "Backpack", None)

        if pack is not None:
            return pack

        return API.FindLayer("backpack", animal.Serial)

    # Opened once a run: ItemsInContainer reads nothing out of a pack the client has never seen
    # inside, and the pack item is safe to double-click where the animal itself is not
    def _room_in(self, pack_serial):
        if pack_serial not in self._opened:
            self._opened.add(pack_serial)
            API.UseObject(pack_serial)
            API.Pause(self._config["open_delay"])

        items = API.ItemsInContainer(pack_serial, True)

        # Unreadable is not empty: moving whole stacks is what the shard's refusal already handles
        if items is None:
            return self._config["capacity"]

        return max(0, self._config["capacity"] - self._wood.board_amount(items))

    def _out_of_reach(self, serial):
        here = API.FindMobile(serial)

        return here is None or here.Distance > self._config["unload_range"]

    # Moves are asynchronous, so rescan between passes rather than trusting MoveItem's return value.
    # A pet that walked off mid-pass has every move refused and looks exactly as full.
    def _move_all(self, serial, pack_serial):
        previous = None

        while not API.StopRequested:
            stacks = self._wood.board_piles()
            total = self._wood.board_amount(stacks)

            if total == 0:
                return "clear"

            if previous is not None and total >= previous:
                if self._out_of_reach(serial) or said(self._config["too_far_text"]):
                    return "lost"

                return "full"

            if self._walk_to(serial) is None:
                return "lost"

            room = self._room_in(pack_serial)

            if room == 0:
                return "full"

            previous = total
            forget(self._config["too_far_text"])

            for stack in stacks:
                part = min(amount_of(stack), room)

                if part == 0:
                    break

                API.MoveItem(stack.Serial, pack_serial, part)
                API.Pause(self._config["move_delay"])
                room -= part

        return "lost"

    # Works down the animals until the pack is clear or every one has had a turn. An animal that
    # stops accepting is full rather than broken, so what is left goes to the next one and that
    # animal is remembered rather than walked to again.
    def _unload_to(self, animals):
        attempted = False
        reached = False

        for animal in animals:
            before = self._wood.board_total()

            if before == 0:
                break

            attempted = True
            here = self._walk_to(animal.Serial)

            if here is None:
                continue

            pack = self._animal_pack(here)

            if pack is None:
                reached = True
                self._log("'%s' has no reachable backpack" % (here.Name or "?"))
                continue

            verdict = self._move_all(animal.Serial, pack.Serial)

            moved = before - self._wood.board_total()
            name = here.Name or "?"

            if verdict == "lost":
                self._log("'%s' moved out of reach while loading, trying it again next haul" % name)
                continue

            reached = True

            if verdict != "full":
                continue

            # A save refuses every move at once, and the caller only asks afterwards - read as
            # this animal's verdict it would sit out the rest of the run over a five second wait
            if self._saves.is_saving():
                self._log("'%s' took nothing while the world is saving, trying the next" % name)
            elif moved == 0:
                self._overloaded.add(animal.Serial)
                self._log("'%s' took nothing, leaving it out of the rest of the run" % name)
            else:
                self._overloaded.add(animal.Serial)
                self._log("'%s' took %d of %d boards and is full, leaving it out of the rest of "
                          "the run" % (name, moved, before))

        # Nothing to load is not a failure to reach anyone
        return reached or not attempted

    # Answers whether an animal was found and reached, not whether anything moved: only a missing
    # animal is worth giving up the search for, and one that took nothing has already been dropped
    def unload(self):
        animals = self.find()

        if len(animals) == 0:
            if not self._reported_no_animal:
                self._reported_no_animal = True
                self._log("no pack animal nearby")

            return "none"

        self._reported_no_animal = False

        # Filtered here rather than in find, which also feeds the trouble watch its companion - an
        # animal that is full is still one worth watching
        spare = [animal for animal in animals if animal.Serial not in self._overloaded]
        reached = True

        if len(spare) == 0:
            if not self._said_all_full:
                self._said_all_full = True
                self._log("all %d pack animal(s) are full, nothing left to load" % len(animals))
        else:
            reached = self._unload_to(spare)

        # A log that leaves as a log never comes back as a board, so what would not convert waits
        # for the next haul to try it again. Asked once every animal has had its turn at the boards.
        if over_buffer(self._config["buffer"]):
            left = self._wood.log_total()

            if left > 0:
                self._log("%d logs would not convert, keeping them in the pack" % left)

        return "tried" if reached else "unreached"

    def haul_now(self):
        before = API.Player.Weight

        self._boards.make_boards()

        outcome = self.unload()

        # A save freezes every part of a haul at once - the conversion is silent, the animal takes
        # nothing, the weight does not move. Read as an ordinary result it latches hauling off.
        if self._saves.is_saving():
            self._saves.wait_out()

            return "hauling"

        if outcome == "none":
            self._hauling = False
            self._log("no pack animal found, carrying on until overweight")

            return "hauling"

        # Not counted against the animals: a haul that never got a pass in range says nothing about
        # whether they are full, and the pets do come back
        if outcome == "unreached":
            self._log("no pack animal in reach this haul, trying again next time")

            return "hauling"

        # Weight rather than stacks moved: what this decides is whether the haul relieved the pack,
        # and an animal that took a stack and refused the rest has not
        if not over_buffer(self._config["buffer"]) or API.Player.Weight < before:
            self._empty_hauls = 0

            return "hauling"

        self._empty_hauls += 1

        if self._empty_hauls >= self._config["max_empty_hauls"]:
            self._hauling = False
            self._log("%d hauls freed nothing - the animals are full. Carrying on until overweight"
                      % self._empty_hauls)

        return "hauling"

    def haul_for_room(self):
        if not over_buffer(self._config["buffer"]):
            return None

        # Once hauling has latched off there is nothing to walk to, so the cycle goes on to chop
        # rather than spending itself on a phase. The conversion still runs, because boards weigh
        # less than the logs they came from and that is worth having with no animal to put them on.
        # Unforced, unlike the one inside a real haul: this runs every cycle from here to the end of
        # the run, and re-trying a wood that has already refused three times would cost three
        # cursors a cycle for the rest of it.
        if not self._hauling:
            self._boards.run()

            return None

        return self.haul_now()
