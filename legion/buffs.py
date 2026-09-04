import time

import API

# Cast in this order within a pass. `buff` is a BuffIconType member name, matched against
# str(buff.Type); `title` is the localized fallback. `mana` is a ceiling - the shard charges a
# paladin less as Chivalry rises - and the client's own Chivalry table says 10 for both.
KEEP = [
    {
        "spell": "Consecrate Weapon",
        "buff": "ConsecrateWeapon",
        "title": "Consecrate Weapon",
        "mana": 10,
        "tithing": 10,
        "needs_weapon": True,
    },
    {
        "spell": "Divine Fury",
        "buff": "DivineFury",
        "title": "Divine Fury",
        "mana": 15,
        "tithing": 10,
    },
]

# Off is a keeper that puts the buffs up and stops. On it keeps them up until you stop the script.
KEEP_UP = True

# Every timing here is in seconds - API.Pause takes seconds where the ClassicUO port took ms.

# Between passes. The buff bar is fed by server packets, so this is how stale the run's picture of
# it can be, and roughly how long a lapsed buff stays down.
POLL = 1.0

# Long enough for the buff packet to land after the incantation, which is what a shard that words
# these differently is read by
CAST_TIMEOUT = 1.0
CAST_WAIT_SLICE = 0.2

# Between two casts inside one pass, to stay under the action throttle
CAST_DELAY = 0.6

# Consecutive casts the shard said nothing readable about, and that put no buff up and spent no
# mana, before the entry is set aside
MAX_MISSES = 5

# How long an entry refused for something a pass cannot fix is left alone before it is tried again
SET_ASIDE = 60.0

# Runs for a day at POLL. A keeper standing over a character with both buffs up is working, so
# nothing here counts cycles against it.
MAX_CYCLES = 100000

MAX_THROTTLED = 20
THROTTLE_BACKOFF = 1.0
THROTTLE_BACKOFF_MAX = 8.0

LOG_EVERY = 25
HEARTBEAT_EVERY = 30.0

SAVE_WAIT = 60.0
SAVE_POLL = 1.0

SAVE_DONE_TEXT = ["World save complete", "Save complete", "World save is complete"]
SAVING_TEXT = ["The world is saving", "Saving world", "World save started"]

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

# Guesses, apart from the tithing wording. Ordered, not a dict: the first bucket holding a match
# wins, which is why alreadyCasting sits before throttled - THROTTLED_TEXT ends in a bare
# 'You must wait' that the longer sentence contains.
OUTCOME_TEXT = [
    # Not depended on: the buff arriving and the mana leaving the pool are the proof
    ("cast", ["Your weapon is consecrated", "You are filled with divine fury"]),
    ("fizzled", ["You fail to cast the spell", "The spell fizzles"]),
    (
        "noTithing",
        [
            "You do not have enough tithing points",
            "You must have at least",
            "You need to make an offering",
        ],
    ),
    ("noMana", ["You do not have enough mana", "Insufficient mana"]),
    ("alreadyUp", ["You are already under the effect"]),
    (
        "noWeapon",
        [
            "You cannot consecrate your fists",
            "You must have a weapon",
            "You must be wielding a weapon",
        ],
    ),
    ("unskilled", ["You are not pious enough", "Your karma is not high enough"] + UNSKILLED_TEXT),
    ("saving", SAVING_TEXT),
    ("alreadyCasting", ["You are already casting a spell", "You are already casting"]),
    ("throttled", THROTTLED_TEXT),
]

STOPPED = "stopped from the script manager"


def log(message):
    API.SysMsg("buffs: " + message)


def backoff_for(count, step, cap):
    return min(step * count, cap)


class Heartbeat(object):
    """Proof of life: a loop standing still in silence looks exactly like a hung one."""

    def __init__(self, every):
        self._every = every
        self._last = None

    # The clock, not the cycle counter: a pass can be a poll or a pair of casts
    def beat(self, phase, cycle, tally):
        moment = time.time()

        if self._last is None:
            self._last = moment
            return

        if moment - self._last < self._every:
            return

        self._last = moment
        log(
            "still here - %s, cycle %d, at %d,%d, %d/%d, %d casts"
            % (
                phase,
                cycle,
                API.Player.X,
                API.Player.Y,
                API.Player.Weight,
                API.Player.WeightMax,
                tally,
            )
        )

    def reset(self):
        self._last = time.time()


heartbeat = Heartbeat(HEARTBEAT_EVERY)


def said(texts):
    for text in texts:
        if API.InJournal(text, False):
            return True

    return False


def is_saving():
    return said(SAVING_TEXT)


# Death only: whoever runs this is in a fight, nothing goes in the pack, and a health floor would
# stop the keeper exactly when the buffs are worth most.
def stop_reason():
    return "you are dead" if API.Player.IsDead else None


def wait_out_save():
    log("the world is saving, waiting it out")

    # Read before the clear: a save can start and finish inside one pass, and clearing first threw
    # the completion away and then stood still for the whole of SAVE_WAIT
    ended = "the shard had already finished" if said(SAVE_DONE_TEXT) else None

    API.ClearJournal()

    waited = 0.0

    while ended is None and waited < SAVE_WAIT:
        API.Pause(SAVE_POLL)
        waited += SAVE_POLL

        if said(SAVE_DONE_TEXT):
            ended = "the shard says it is done"
        elif stop_reason() is not None:
            ended = "the run has a reason to stop"

    log("%s, carrying on" % (ended or "nothing said in %ds" % int(SAVE_WAIT)))

    heartbeat.reset()


dumped = False


# ApiBuff never refreshes after it is handed over, so the bar is re-read every time it matters
def standing(entry):
    global dumped

    buffs = API.ActiveBuffs()

    if buffs and not dumped:
        dumped = True
        log("buff bar: " + ", ".join("%s/%s" % (b.Type, b.Title or "") for b in buffs))

    for buff in buffs:
        if str(buff.Type) == entry["buff"]:
            return True

        if entry["title"] and entry["title"].lower() in (buff.Title or "").lower():
            return True

    return False


# Either hand: a katana is one-handed and a no-dachi two-handed, and Consecrate Weapon takes both
def armed():
    return API.FindLayer("twohanded") is not None or API.FindLayer("onehanded") is not None


def matched_bucket():
    for name, phrases in OUTCOME_TEXT:
        # clearMatches, or a line already read answers the next cast's wait as well
        if API.InJournalAny(phrases, True):
            return name

    return None


def cast_once(entry):
    up_before = standing(entry)

    # Re-issuing a buff that is already standing is the one thing this script exists not to do
    if up_before:
        return "alreadyUp"

    mana_before = API.Player.Mana

    # Cancelled only when there is one to cancel: an unconditional cancel just before an action left
    # the next cursor unusable in the run this was copied from
    if API.HasTarget():
        API.CancelTarget()

    API.ClearJournal()
    API.CastSpell(entry["spell"])

    waited = 0.0

    while waited < CAST_TIMEOUT:
        hit = matched_bucket()

        if hit is not None:
            return hit

        API.Pause(CAST_WAIT_SLICE)
        waited += CAST_WAIT_SLICE

    # The proofs that do not go through the journal. A transition, not a state: one already standing
    # proves nothing, which is why up_before was read first.
    if standing(entry):
        return "cast"

    if API.Player.Mana < mana_before:
        return "cast"

    return None


table = [
    {"entry": entry, "name": entry["spell"], "misses": 0, "until": 0.0, "retired": None}
    for entry in KEEP
]

casts = 0
reported = 0
throttled = 0
stop = None

# Said once per stretch rather than once per pass, or an unarmed character scrolls the journal at
# POLL for as long as they stay unarmed
said_unarmed = False
said_short = False
said_untithed = False

proved = set()


def due(item):
    return item["retired"] is None and time.time() >= item["until"]


def set_aside(item, for_seconds):
    item["misses"] = 0
    item["until"] = time.time() + for_seconds


def retire(item, why):
    item["retired"] = why


# The run has nothing left to do: every entry refused for a reason no later pass can change
def spent():
    return all(item["retired"] is not None for item in table)


# What a KEEP_UP=False run waits for. A retired entry counts as settled or it would never finish.
def settled():
    return all(item["retired"] is not None or standing(item["entry"]) for item in table)


# The first cast of each spell, so a wrong OUTCOME_TEXT or a wrong buff id shows up in the first
# minute rather than as a run that quietly never casts
def say_first(item):
    if item["name"] in proved:
        return

    proved.add(item["name"])
    log("%s up" % item["name"])


def back_off():
    global throttled, stop

    throttled += 1

    if throttled >= MAX_THROTTLED:
        stop = "the shard refused %d casts in a row" % MAX_THROTTLED
        return

    API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))


def put_up(item):
    global casts, throttled

    outcome = cast_once(item["entry"])

    if outcome == "cast":
        casts += 1
        throttled = 0
        item["misses"] = 0
        say_first(item)

    # The shard answered, so the table is right and the roll simply lost. Next pass tries again.
    elif outcome in ("fizzled", "alreadyUp"):
        throttled = 0
        item["misses"] = 0

    # The gate above cleared, so this entry's mana figure is understated for this shard
    elif outcome == "noMana":
        item["misses"] = 0
        log(
            "%s costs more than %d mana here - raise it in KEEP"
            % (item["name"], item["entry"]["mana"])
        )

    # Nothing a script does refills tithing points, so this entry is finished for the run
    elif outcome == "noTithing":
        retire(item, "out of tithing points - tithe gold at a shrine")

    elif outcome == "unskilled":
        retire(item, "the shard refuses it at this skill or karma")

    # The hand check above missed it, so believe the shard rather than the client's layers
    elif outcome == "noWeapon":
        set_aside(item, SET_ASIDE)

    elif outcome == "saving":
        wait_out_save()

    elif outcome in ("cooldown", "throttled", "alreadyCasting"):
        back_off()

    # Nothing said, no buff, and no mana left the pool: whatever this was, it did not happen
    else:
        item["misses"] += 1

        if item["misses"] >= MAX_MISSES:
            set_aside(item, SET_ASIDE)
            log(
                "%s did nothing %d times - set aside; check OUTCOME_TEXT"
                % (item["name"], MAX_MISSES)
            )


def one_pass():
    global said_unarmed, said_short, said_untithed

    hands = armed()

    if hands:
        said_unarmed = False

    for item in table:
        if stop is not None or not due(item):
            continue

        if standing(item["entry"]):
            item["misses"] = 0
            continue

        entry = item["entry"]

        if entry.get("needs_weapon") and not hands:
            if not said_unarmed:
                said_unarmed = True
                log("nothing in hand - %s is waiting for you to draw something" % item["name"])

            continue

        if API.Player.Mana < entry["mana"]:
            if not said_short:
                said_short = True
                log(
                    "%d/%d mana for %s - waiting for it"
                    % (API.Player.Mana, entry["mana"], item["name"])
                )

            continue

        said_short = False

        # Not in the ClassicUO run, which had no tithing gate: a noTithing retires the entry for the
        # whole run, so a character who forgot to tithe would lose every buff on the first pass
        if API.Player.TithingPoints < entry["tithing"]:
            if not said_untithed:
                said_untithed = True
                log(
                    "%d/%d tithing points for %s - tithe gold at a shrine"
                    % (API.Player.TithingPoints, entry["tithing"], item["name"])
                )

            continue

        said_untithed = False

        put_up(item)
        API.Pause(CAST_DELAY)


log("keeping %s up" % " and ".join(item["name"] for item in table))

if not armed() and any(item["entry"].get("needs_weapon") for item in table):
    log("nothing in hand - the weapon enchants will be refused until you draw something")

log("%d tithing points; every cast spends some, tithe gold at a shrine" % API.Player.TithingPoints)

for cycle in range(MAX_CYCLES):
    if stop is not None:
        break

    if API.StopRequested:
        stop = STOPPED
        break

    stop = stop_reason()

    if stop is not None:
        break

    if is_saving():
        wait_out_save()
        continue

    one_pass()

    if stop is not None:
        break

    if spent():
        stop = "every buff was refused for good"
        break

    if not KEEP_UP and settled():
        stop = "everything that could go up is up"
        break

    if casts >= reported + LOG_EVERY:
        reported = casts
        log("%d casts, %d/%d mana" % (casts, API.Player.Mana, API.Player.ManaMax))

    heartbeat.beat("watching the buff bar", cycle, casts)
    API.Pause(POLL)

for item in table:
    if item["retired"] is not None:
        log("%s was set aside - %s" % (item["name"], item["retired"]))

reason = stop or "hit the %d cycle backstop" % MAX_CYCLES

log("%d casts, stopping - %s" % (casts, reason))
API.Stop()
