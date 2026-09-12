import API

from uo.entity import find_mobile


class Hunt(object):
    """The animals this run is finished with, and the scan that leaves them out."""

    def __init__(self, pet_name, radius, opl_timeout):
        self._pet_name = pet_name
        self._radius = radius
        self._opl_timeout = opl_timeout
        self._skipped = set()

    def leave_out(self, serial):
        self._skipped.add(serial)

    def mine(self, name):
        return self._pet_name != "" and name.lower() == self._pet_name.lower()

    # Names read empty until the client has tooltip data, so the one about to be taken is asked for
    # by tooltip rather than every candidate on every scan
    def named(self, mobile):
        if mobile.Name:
            return mobile.Name

        props = mobile.NameAndProps(True, self._opl_timeout) or ""
        first = props.splitlines()[0].strip() if props else ""

        return first or hex(mobile.Serial)

    def next_quarry(self, graphic):
        # 0 asks for every animal: GetAllMobiles already treats distance=None as unlimited
        distance = self._radius if self._radius > 0 else None

        candidates = [
            mobile
            for mobile in API.GetAllMobiles(graphic=graphic, distance=distance)
            if not mobile.IsDestroyed
            and mobile.Serial not in self._skipped
            and not mobile.IsDead
            # True for pets and followers, so this is every animal the run has already kept
            and not mobile.IsRenamable
            and not self.mine(mobile.Name or "")
        ]

        for mobile in candidates:
            name = self.named(mobile)

            # Released under the name rather than kept, so nothing but the name says it was yours
            if self.mine(name):
                self.leave_out(mobile.Serial)
                continue

            return (
                {"serial": mobile.Serial, "name": name, "graphic": mobile.Graphic},
                len(candidates),
            )

        return None


def is_pet(serial):
    found = find_mobile(serial)

    return found is not None and found.IsRenamable
