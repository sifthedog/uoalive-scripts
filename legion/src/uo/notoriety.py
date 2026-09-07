"""Passed through to the scans, never compared or OR-ed: the API.py stub lists every value as 1."""

import API

# Innocent is out, or every blue NPC in the world is trouble
HOSTILE = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]
