"""A fake Legion API, reachable the two ways the real one is: as a builtin, and as `import API`.

Deliberately inert - nothing is found, the journal is empty, every wait succeeds and Pause does not
sleep. A test that depends on an outcome has to say so, so the fixture never quietly supplies the
thing under test.
"""

import builtins
import sys


class FakeSkill(object):
    def __init__(self, value=0.0, cap=100.0):
        self.Value = value
        self.Cap = cap
        self.Base = value


class FakeItem(object):
    def __init__(self, **fields):
        self.Serial = fields.get("serial", 0x40000000)
        self.Graphic = fields.get("graphic", 0)
        self.Hue = fields.get("hue", 0)
        self.Amount = fields.get("amount", 1)
        self.Name = fields.get("name", "")
        self.Container = fields.get("container", 0)
        self.X = fields.get("x", 0)
        self.Y = fields.get("y", 0)
        self.Z = fields.get("z", 0)
        self.Layer = fields.get("layer", "")


class FakeMobile(object):
    def __init__(self, **fields):
        self.Serial = fields.get("serial", 0x00010000)
        self.Graphic = fields.get("graphic", 0)
        self.Hue = fields.get("hue", 0)
        self.Name = fields.get("name", "")
        self.Distance = fields.get("distance", 0)
        self.IsDead = fields.get("is_dead", False)
        self.IsRenamable = fields.get("is_renamable", False)
        self.Notoriety = fields.get("notoriety", 1)
        self.Backpack = fields.get("backpack", None)
        self.Hits = fields.get("hits", 100)
        self.HitsMax = fields.get("hits_max", 100)
        self.X = fields.get("x", 0)
        self.Y = fields.get("y", 0)
        self.Z = fields.get("z", 0)


class FakePlayer(object):
    def __init__(self, **fields):
        self.Serial = fields.get("serial", 0x00000001)
        self.Name = fields.get("name", "tester")
        self.X = fields.get("x", 1000)
        self.Y = fields.get("y", 1000)
        self.Z = fields.get("z", 0)
        self.IsDead = fields.get("is_dead", False)
        self.IsCasting = fields.get("is_casting", False)
        self.TithingPoints = fields.get("tithing_points", 100)
        # 100/100 and 50/50 rather than 0: a 0 here is the stat-refresh fault, not a healthy player
        self.Hits = fields.get("hits", 100)
        self.HitsMax = fields.get("hits_max", 100)
        self.Mana = fields.get("mana", 50)
        self.ManaMax = fields.get("mana_max", 50)
        self.Weight = fields.get("weight", 100)
        self.WeightMax = fields.get("weight_max", 400)
        self.Followers = fields.get("followers", 0)
        self.FollowersMax = fields.get("followers_max", 5)


class FakeAPI(object):
    def __init__(self):
        self.Player = FakePlayer()
        self.Backpack = 0x40000000
        self.StopRequested = False

        self.messages = []
        self.journal = []
        self.paused = 0.0
        self.pauses = []
        self.stopped = False
        self.cleared = 0
        self.cancelled_pathfinding = 0
        self.cancelled_targets = 0

        self.containers = {}
        self.items = {}
        self.mobiles = {}
        self.skills = {}

        self.has_target = False
        self.pathfinding = False
        self.requested_target = 0

        self.buffs = []
        self.layers = {}
        self.cast = []
        self.used_skills = []
        self.used = []
        self.targeted = []
        self.pre_targeted = []
        self.cancelled_pre_targets = 0
        self.moved = []

    def SysMsg(self, text, hue=None):
        self.messages.append(text)

    def Pause(self, seconds):
        self.paused += seconds
        self.pauses.append(seconds)

    def Stop(self):
        self.stopped = True

    def ClearJournal(self):
        self.cleared += 1
        self.journal = []

    def GetJournalEntries(self):
        return list(self.journal)

    def InJournal(self, text, clear_matches=False):
        low = text.lower()
        hits = [line for line in self.journal if low in line.lower()]

        if hits and clear_matches:
            self.journal = [line for line in self.journal if low not in line.lower()]

        return bool(hits)

    def InJournalAny(self, texts, clear_matches=False):
        for text in texts:
            if self.InJournal(text, clear_matches):
                return True

        return False

    def ItemsInContainer(self, serial, recurse=False):
        held = self.containers.get(serial, [])

        return list(held) if held is not None else None

    def FindItem(self, serial):
        return self.items.get(serial)

    def FindMobile(self, serial):
        return self.mobiles.get(serial)

    def GetSkill(self, name):
        return self.skills.get(name)

    def HasTarget(self, kind="any"):
        return self.has_target

    def CancelTarget(self):
        self.cancelled_targets += 1
        self.has_target = False

    def Pathfinding(self):
        return self.pathfinding

    def CancelPathfinding(self):
        self.cancelled_pathfinding += 1
        self.pathfinding = False

    def ActiveBuffs(self):
        return list(self.buffs)

    def FindLayer(self, layer, serial=None):
        return self.layers.get(layer)

    def CastSpell(self, spell):
        self.cast.append(spell)

    def UseSkill(self, name):
        self.used_skills.append(name)

    def UseObject(self, serial):
        self.used.append(serial)

    def Target(self, *args):
        self.targeted.append(args)
        self.has_target = False

    def TargetSelf(self):
        self.targeted.append(("self",))
        self.has_target = False

    def PreTarget(self, serial, kind=None):
        self.pre_targeted.append((serial, kind))

    def CancelPreTarget(self):
        self.cancelled_pre_targets += 1

    def RequestTarget(self, timeout=None):
        return self.requested_target

    def WaitForTarget(self, kind="any", timeout=None):
        return self.has_target

    def MoveItem(self, serial, container, amount=-1):
        self.moved.append((serial, container, amount))

        return True

    def hear(self, *lines):
        self.journal.extend(lines)

    def hold(self, *items):
        self.containers[self.Backpack] = list(items)

        for held in items:
            self.items[held.Serial] = held


_current = [FakeAPI()]


class _Proxy(object):
    """Modules bind `API` once at import; the proxy is what lets install() hand out a fresh world."""

    def __getattr__(self, name):
        return getattr(_current[0], name)

    def __setattr__(self, name, value):
        setattr(_current[0], name, value)


_proxy = _Proxy()

builtins.API = _proxy
sys.modules.setdefault("API", _proxy)


def install():
    _current[0] = FakeAPI()

    return _current[0]


def item(**fields):
    return FakeItem(**fields)


def mobile(**fields):
    return FakeMobile(**fields)


def skill(value=0.0, cap=100.0):
    return FakeSkill(value, cap)
