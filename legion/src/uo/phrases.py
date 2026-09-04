"""The shard's own wordings, as far as they are the same whatever the script is doing."""

SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]
SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]

# Ends in a bare 'You must wait', which longer refusals contain - so a bucket that has to be told
# apart from a throttle is ordered before this one
THROTTLED_TEXT = [
    "You must wait to perform another action",
    "You must wait a moment",
    "You must wait",
]

UNSKILLED_TEXT = [
    "You are not skilled enough",
    "You lack the required skill",
    "You do not have enough skill",
]

STOPPED = "stopped from the script manager"

NO_GUARDS_TEXT = [
    "The guards can not be called here",
    "The guards cannot be called here",
    "Guards can not be called here",
    "Guards cannot be called here",
    "There are no guards here",
    "guards cannot be summoned here",
]

GUARD_ZONE_TEXT = ["under the protection of the town guards", "now under guard"]
UNGUARDED_TEXT = ["left the protection of the town guards", "no longer under guard"]

# Empty on purpose: nothing in stock RunUO announces being attacked, and a wrong guess calls the
# guards every cycle of a quiet run
ATTACK_TEXT = []
