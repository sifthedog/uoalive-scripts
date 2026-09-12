# Read off the gump as one token per row and the number after it: 'OakBoard 850', boards then logs,
# a row only while the box holds any. The buttons are read off the gump's layout; the table is the
# fallback, right only while every board row is up, since a missing row shifts the ids after it.
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
        "Log": ("logs", None),
        "OakLog": ("logs", "oak"),
        "AshLog": ("logs", "ash"),
        "YewLog": ("logs", "yew"),
        "HeartwoodLog": ("logs", "heartwood"),
        "BloodwoodLog": ("logs", "bloodwood"),
        "FrostwoodLog": ("logs", "frostwood"),
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
