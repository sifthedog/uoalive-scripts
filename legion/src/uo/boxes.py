# Read off the gump as one token per row and the number after it: 'OakBoard 850'. The buttons are
# read off the gump's layout; the table is the fallback, as box-probe.py read them on UOAlive.
WOOD_BOX = {
    "names": ["storage box"],
    "graphics": set(),
    "title": ["storage box"],
    "rows": {
        "Board": ("boards", None),
        "OakBoard": ("boards", "oak"),
        "AshBoard": ("boards", "ash"),
        "YewBoard": ("boards", "yew"),
        "HeartwoodBoard": ("boards", "heartwood"),
        "BloodwoodBoard": ("boards", "bloodwood"),
        "FrostwoodBoard": ("boards", "frostwood"),
    },
    "buttons": {
        "Board": 107,
        "OakBoard": 108,
        "AshBoard": 109,
        "YewBoard": 110,
        "HeartwoodBoard": 111,
        "BloodwoodBoard": 112,
        "FrostwoodBoard": 113,
    },
}
