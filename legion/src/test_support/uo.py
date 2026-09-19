"""A fake Legion API, reachable the two ways the real one is: as a builtin, and as `import API`.

Deliberately inert - nothing is found, the journal is empty, every wait succeeds and Pause does not
sleep. A test that depends on an outcome has to say so, so the fixture never quietly supplies the
thing under test.
"""

import builtins
import sys
import types


class FakeEntry(object):
    def __init__(self, text, name="System"):
        self.Text = text
        self.Name = name


# A test that puts a plain string in the journal is the shard talking; overhear() names anyone else
def _heard(entry):
    return entry if isinstance(entry, tuple) else ("System", entry)


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
        self.IsContainer = fields.get("is_container", False)
        self.Opened = fields.get("opened", False)


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
        self.IsDestroyed = fields.get("is_destroyed", False)
        self.IsHuman = fields.get("is_human", False)
        self.Hits = fields.get("hits", 100)
        self.HitsMax = fields.get("hits_max", 100)
        self.X = fields.get("x", 0)
        self.Y = fields.get("y", 0)
        self.Z = fields.get("z", 0)
        self.props = fields.get("props", "")

    def NameAndProps(self, force=False, timeout=None):
        return self.props


_DIRECTION_NAMES = {
    "north": "North",
    "northeast": "Right", "right": "Right",
    "east": "East",
    "southeast": "Down", "down": "Down",
    "south": "South",
    "southwest": "Left", "left": "Left",
    "west": "West",
    "northwest": "Up", "up": "Up",
}


class FakeNotoriety(object):
    Innocent = 1
    Ally = 2
    Gray = 3
    Criminal = 4
    Enemy = 5
    Murderer = 6
    Invulnerable = 7


class FakePlayer(object):
    def __init__(self, **fields):
        self.Serial = fields.get("serial", 0x00000001)
        self.Name = fields.get("name", "tester")
        self.X = fields.get("x", 1000)
        self.Y = fields.get("y", 1000)
        self.Z = fields.get("z", 0)
        self.Direction = fields.get("direction", "North")
        self.IsDead = fields.get("is_dead", False)
        self.IsCasting = fields.get("is_casting", False)
        self.IsMounted = fields.get("is_mounted", False)
        self.TithingPoints = fields.get("tithing_points", 100)
        # 100/100 and 50/50 rather than 0: a 0 here is the stat-refresh fault, not a healthy player
        self.Hits = fields.get("hits", 100)
        self.HitsMax = fields.get("hits_max", 100)
        self.Mana = fields.get("mana", 50)
        self.ManaMax = fields.get("mana_max", 50)
        self.LowerManaCost = fields.get("lower_mana_cost", 0)
        self.Weight = fields.get("weight", 100)
        self.WeightMax = fields.get("weight_max", 400)
        self.Followers = fields.get("followers", 0)
        self.FollowersMax = fields.get("followers_max", 5)


class FakeGui(object):
    def __init__(self, serial):
        self.ServerSerial = serial


class FakeButton(object):
    def __init__(self, button):
        self.ButtonID = button


class FakeHtml(object):
    def __init__(self, text):
        self.Text = text


class FakeGump(object):
    def __init__(self, children, layout=None):
        self.Children = children
        self.PacketGumpText = layout


class FakeControl(object):
    def __init__(self, kind, text=""):
        self.kind = kind
        self.text = text
        self.children = []
        self.rect = None
        self.centered = 0
        self.IsDisposed = False
        self.IsVisible = True

    def SetRect(self, x, y, width, height):
        self.rect = (x, y, width, height)
        return self

    def SetPos(self, x, y):
        self.rect = (x, y) + ((self.rect or (0, 0, 0, 0))[2:])
        return self

    def SetWidth(self, width):
        return self

    def SetHeight(self, height):
        return self

    def SetText(self, text):
        self.text = text

    def CenterXInViewPort(self):
        self.centered += 1
        return self

    def CenterYInViewPort(self):
        self.centered += 1
        return self

    def Add(self, child):
        self.children.append(child)

    def Dispose(self):
        self.IsDisposed = True


class FakeDrawnButton(FakeControl):
    def __init__(self, text):
        FakeControl.__init__(self, "button", text)
        self.clicked = False
        self.on_click = []


class FakeToggle(FakeControl):
    def __init__(self, kind, text, group, checked):
        FakeControl.__init__(self, kind, text)
        self.group = group
        self.IsChecked = checked

    def GetIsChecked(self):
        return self.IsChecked

    def SetIsChecked(self, checked):
        self.IsChecked = checked


class FakeTextBox(FakeControl):
    def __init__(self, text):
        FakeControl.__init__(self, "textbox", text)

    @property
    def Text(self):
        return self.text

    @Text.setter
    def Text(self, text):
        self.text = text


class FakeDropDown(FakeControl):
    def __init__(self, items, index):
        FakeControl.__init__(self, "dropdown", items[index] if items else "")
        self.items = list(items)
        self.index = index
        self.on_select = []

    def GetSelectedIndex(self):
        return self.index

    def OnDropDownOptionSelected(self, callback):
        self.on_select.append(callback)
        return self


class FakeGumps(object):
    def __init__(self, api):
        self._api = api

    def CreateGump(self, acceptMouseInput=True, canMove=True, keepOpen=False):
        if self._api.StopRequested:
            return None

        return FakeControl("gump")

    def CreateGumpColorBox(self, opacity=0.7, color="#000000"):
        return FakeControl("box", color)

    def CreateGumpLabel(self, text, hue=996):
        return FakeControl("label", text)

    def CreateSimpleButton(self, text, width, height):
        return FakeDrawnButton(text)

    def CreateGumpTTFLabel(self, text, size, color="#FFFFFF", font=None, aligned="left",
                           maxWidth=0, applyStroke=False):
        label = FakeControl("ttf", text)
        label.color = color
        return label

    def CreateGumpRadioButton(self, text="", group=0, inactive=0, active=0, hue=0,
                              isChecked=False):
        return FakeToggle("radio", text, group, isChecked)

    def CreateGumpCheckbox(self, text="", hue=0, isChecked=False):
        return FakeToggle("checkbox", text, None, isChecked)

    def CreateDropDown(self, width, items, selectedIndex=0):
        return FakeDropDown(items, selectedIndex)

    def CreateGumpTextBox(self, text="", width=200, height=30, multiline=False, fontSize=20):
        return FakeTextBox(text)

    def AddControlOnClick(self, control, onClick, leftOnly=True):
        control.on_click.append(onClick)
        return control

    def AddGump(self, gump):
        self._api.drawn.append(gump)


class FakeAPI(object):
    def __init__(self):
        self.Player = FakePlayer()
        self.map = 0
        self.Backpack = 0x40000000
        self.StopRequested = False
        self.ScriptPath = ""
        self.Notoriety = FakeNotoriety
        self.Gumps = FakeGumps(self)

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
        self.dropped = []
        self.turned = []
        self.renamed = []
        self.menu_entries = set()
        self.menus = []
        self.gump = 0
        self.open_gumps = set()
        self.gump_buttons = {}
        # Controls handed back as given, in order: FakeButton and FakeHtml, for a menu read whole
        self.gump_controls = {}
        self.gump_layouts = {}
        self.gump_text = []
        self.gump_contents = {}
        self.opens = {}
        self.replies = []
        self.closed_gumps = 0
        self.drawn = []
        self.pathfound = []
        self.reachable = False
        self.land = {}
        self.statics = {}
        self.paths = {}
        self.path_probes = []
        self.opl_requests = []
        self.forgotten = []
        self.props = {}
        self.equipped = []
        self.dismounts = 0
        self.said_aloud = []
        self.head_messages = []
        self.launched = []
        self.processes = []
        self.launch_error = None
        self.attacked = []
        self.war_mode = None

    def SysMsg(self, text, hue=None):
        self.messages.append(text)

    def Pause(self, seconds):
        self.paused += seconds
        self.pauses.append(seconds)

    def Stop(self):
        self.stopped = True

    def ClearJournal(self, matching=""):
        self.cleared += 1

        if matching:
            self.forgotten.append(matching)
            self.journal = [entry for entry in self.journal
                            if matching not in _heard(entry)[1]]
        else:
            self.journal = []

    def GetJournalEntries(self, seconds=None):
        return [FakeEntry(text, name)
                for name, text in (_heard(entry) for entry in self.journal)]

    def InJournal(self, text, clear_matches=False):
        low = text.lower()
        hits = [entry for entry in self.journal if low in _heard(entry)[1].lower()]

        if hits and clear_matches:
            self.journal = [entry for entry in self.journal
                            if low not in _heard(entry)[1].lower()]

        return bool(hits)

    def InJournalAny(self, texts, clear_matches=False):
        for text in texts:
            if self.InJournal(text, clear_matches):
                return True

        return False

    # The client throws on a null container rather than answering none, which is what a stopping
    # script reads the backpack as
    def ItemsInContainer(self, serial, recurse=False):
        if not serial:
            raise ValueError("Arg_NullReferenceException")

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

        if serial in self.opens:
            self.gump = self.opens[serial]

    # Player.Direction reports ClassicUO's own enum names, not the compass words Turn() takes in -
    # "northeast"/"right" both land on "Right", the same aliasing fishing.direction.NAMES relies on
    def Turn(self, direction):
        name = _DIRECTION_NAMES.get((direction or "").lower())

        if name is not None and self.Player.Direction != name:
            self.turned.append(direction)
            self.Player.Direction = name

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

    def MoveItemOffset(self, serial, amount=0, x=0, y=0, z=0, OSI=False):
        self.dropped.append((serial, amount, x, y, z))

        return True

    def GetMap(self):
        return self.map

    def GetTile(self, x, y):
        return self.land.get((x, y))

    def GetStaticsAt(self, x, y):
        return list(self.statics.get((x, y), []))

    def GetStaticsInArea(self, x1, y1, x2, y2):
        found = []

        for (x, y), here in self.statics.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                found.extend(here)

        return found

    def GetPath(self, x, y, z, within=0):
        self.path_probes.append((x, y))

        return self.paths.get((x, y, within), self.paths.get((x, y)))

    def Pathfind(self, x, y, z, within=0, wait=False, timeout=None):
        self.pathfound.append(((x, y, z), within))

        return True

    def ItemNameAndProps(self, serial, force=False, timeout=None):
        return self.props.get(serial, "")

    def RequestOPLData(self, serials):
        self.opl_requests.append(list(serials))

    def EquipItem(self, serial):
        self.equipped.append(serial)

    def Dismount(self):
        self.dismounts += 1

    def Msg(self, text):
        self.said_aloud.append(text)

    def HeadMsg(self, text, serial, hue=None):
        self.head_messages.append((text, serial, hue))

    def GetAllMobiles(self, graphic=None, distance=None, notoriety=None):
        return [m for m in self.mobiles.values()
                if (graphic is None or m.Graphic == graphic)
                and (distance is None or m.Distance <= distance)
                and (notoriety is None or m.Notoriety in notoriety)]

    def SetWarMode(self, enabled):
        self.war_mode = enabled

    def Attack(self, serial):
        self.attacked.append(serial)

    def PathfindEntity(self, serial, within, wait=False, timeout=None, run=False):
        self.pathfound.append((serial, within))

        return self.reachable

    def ContextMenu(self, serial, text, timeout=None):
        self.menus.append((serial, text))

        return text in self.menu_entries

    def HasGump(self):
        return self.gump

    def _open_gumps(self):
        return set(self.open_gumps) | (set([self.gump]) if self.gump else set())

    def WaitForGump(self, ID=None, delay=5):
        return bool(ID) and ID in self._open_gumps()

    def GetAllGumps(self):
        return [FakeGui(serial) for serial in sorted(self._open_gumps())]

    def GetGump(self, ID=None):
        if ID in self.gump_controls:
            return FakeGump(self.gump_controls[ID], self.gump_layouts.get(ID))

        if ID not in self.gump_buttons and ID not in self.gump_layouts:
            return None

        return FakeGump([FakeButton(button) for button in self.gump_buttons.get(ID, [])],
                        self.gump_layouts.get(ID))

    def GumpContains(self, text, gump=None):
        return any(text.lower() in line.lower() for line in self.gump_text)

    def GetGumpContents(self, gump=None):
        return self.gump_contents.get(gump, "")

    def ReplyGump(self, button, gump=None):
        self.replies.append((button, gump))

        return bool(self.gump)

    def CloseGump(self, gump=None):
        self.closed_gumps += 1
        self.gump = 0

    def ProcessCallbacks(self):
        for button in self.drawn_buttons():
            if button.clicked:
                button.clicked = False

                for callback in button.on_click:
                    callback()

    def drawn_controls(self, roots=None):
        found = []

        for control in (self.drawn if roots is None else roots):
            found.append(control)
            found.extend(self.drawn_controls(control.children))

        return found

    def drawn_buttons(self):
        return [control for control in self.drawn_controls()
                if isinstance(control, FakeDrawnButton)]

    def press(self, text):
        for button in self.drawn_buttons():
            if button.text == text:
                button.clicked = True

    def check(self, text):
        toggles = [control for control in self.drawn_controls()
                   if isinstance(control, FakeToggle)]

        for toggle in toggles:
            if toggle.text == text:
                for other in toggles:
                    if other.group is not None and other.group == toggle.group:
                        other.IsChecked = False

                toggle.IsChecked = True

    def uncheck(self, text):
        for control in self.drawn_controls():
            if isinstance(control, FakeToggle) and control.text == text:
                control.IsChecked = False

    def select(self, index):
        dropdown = [control for control in self.drawn_controls()
                    if isinstance(control, FakeDropDown)][-1]
        dropdown.index = index
        dropdown.text = dropdown.items[index]

        for callback in dropdown.on_select:
            callback(index)

    def texts(self):
        return [control.text for control in self.drawn_controls()
                if control.kind in ("label", "ttf")]

    def text_boxes(self):
        return [control for control in self.drawn_controls() if isinstance(control, FakeTextBox)]

    def type_into(self, index, text):
        self.text_boxes()[index].Text = text

    def visible(self, text):
        return any(control.IsVisible for control in self.drawn_controls()
                   if control.text == text)

    def close_drawn(self):
        self.drawn[-1].Dispose()

    def Rename(self, serial, name):
        self.renamed.append((serial, name))

    def see(self, *mobiles):
        for seen in mobiles:
            self.mobiles[seen.Serial] = seen

    def hear(self, *lines):
        self.journal.extend(lines)

    def overhear(self, name, *lines):
        self.journal.extend((name, line) for line in lines)

    def hold(self, *items):
        self.containers[self.Backpack] = list(items)

        for held in items:
            self.items[held.Serial] = held

    def take(self, *serials):
        for container in self.containers:
            self.containers[container] = [held for held in self.containers[container]
                                          if held.Serial not in serials]

        for serial in serials:
            self.items.pop(serial, None)


_current = [FakeAPI()]


class FakeProcess(object):
    def __init__(self, command):
        self.command = command
        self.HasExited = False
        self.killed = False

    def Kill(self):
        self.killed = True
        self.HasExited = True


class _Arguments(list):
    Add = list.append


class FakeStartInfo(object):
    def __init__(self):
        self.FileName = ""
        self.UseShellExecute = True
        self.CreateNoWindow = False
        self.ArgumentList = _Arguments()


class FakeProcessClass(object):
    @staticmethod
    def Start(info):
        if _current[0].launch_error is not None:
            raise _current[0].launch_error

        process = FakeProcess([info.FileName] + list(info.ArgumentList))
        _current[0].launched.append(process.command)
        _current[0].processes.append(process)

        return process


def _dotnet():
    clr = types.ModuleType("clr")
    clr.AddReference = lambda name: None
    system = types.ModuleType("System")
    system.Diagnostics = types.ModuleType("System.Diagnostics")
    system.Diagnostics.Process = FakeProcessClass
    system.Diagnostics.ProcessStartInfo = FakeStartInfo

    return clr, system


class _Proxy(object):
    """Modules bind `API` once at import; the proxy is what lets install() hand out a fresh world."""

    def __getattr__(self, name):
        return getattr(_current[0], name)

    def __setattr__(self, name, value):
        setattr(_current[0], name, value)


_proxy = _Proxy()

builtins.API = _proxy
sys.modules.setdefault("API", _proxy)

_clr, _system = _dotnet()
sys.modules.setdefault("clr", _clr)
sys.modules.setdefault("System", _system)


def install():
    _current[0] = FakeAPI()

    return _current[0]


def item(**fields):
    return FakeItem(**fields)


def mobile(**fields):
    return FakeMobile(**fields)


def skill(value=0.0, cap=100.0):
    return FakeSkill(value, cap)


def static(x=0, y=0, z=0, graphic=0, name="", is_tree=False, is_vegetation=False):
    return FakeStatic(x, y, z, graphic, name, is_tree, is_vegetation)


class FakePoint(object):
    def __init__(self, x, y, z=0):
        self.X = x
        self.Y = y
        self.Z = z


def point(x, y, z=0):
    return FakePoint(x, y, z)


def tile(x, y, z=0, graphic=0, is_land=True, name=""):
    return {"x": x, "y": y, "z": z, "graphic": graphic, "is_land": is_land, "name": name}


class FakeStatic(object):
    def __init__(self, x=0, y=0, z=0, graphic=0, name="", is_tree=False, is_vegetation=False):
        self.X = x
        self.Y = y
        self.Z = z
        self.Graphic = graphic
        self.Name = name
        self.IsTree = is_tree
        self.IsVegetation = is_vegetation


class FakeLand(object):
    def __init__(self, z=0, graphic=0):
        self.Z = z
        self.Graphic = graphic
