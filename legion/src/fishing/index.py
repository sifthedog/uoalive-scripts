import API

from fishing.angler import Angler
from fishing.config import (CAST_POLL, CAST_TIMEOUT, CATCH_POLL, CATCH_SETTLE, CAUGHT_TEXT,
                            CURSOR_POLL, CURSOR_TIMEOUT, DATA_PATH, DISMOUNT_ATTEMPTS,
                            DISMOUNT_POLL, DISMOUNT_TIMEOUT, FISH_RANGE, GAIN_POLL, GAIN_SETTLE,
                            GUARD_PHRASE, HAND_LAYERS, JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS,
                            NO_CURSOR_READ, OUTCOME_TEXT, POLE_GRAPHICS, POLE_NAME_WORDS,
                            PROMPT_TEXT, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT,
                            WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS)
from fishing.pole import find_pole
from fishing.water import nearest_water
from uo.guards import dead, first_reason, skill_capped
from uo.journal import journal_tail
from uo.log import make_log
from uo.mount import dismount
from uo.pack import counts_by_graphic, diff_counts, pack_contents
from uo.record import attempt_log
from uo.retry import settled
from uo.skill import SkillReader, find_skill_name, reading
from uo.terrain import Terrain

log = make_log("fishing")

CAST_CONFIG = {
    "cursor_timeout": CURSOR_TIMEOUT,
    "cursor_poll": CURSOR_POLL,
    "prompt_text": PROMPT_TEXT,
    "no_cursor_read": NO_CURSOR_READ,
    "cast_timeout": CAST_TIMEOUT,
    "cast_poll": CAST_POLL,
    "caught_text": CAUGHT_TEXT,
    "tail_seconds": JOURNAL_TAIL_SECONDS,
    "tail_lines": JOURNAL_TAIL_LINES,
}

ENDINGS = {
    "failed": "nothing bit",
    "empty": "the fish are not biting here - try further along the shore",
    "tooFar": "the shard says the water is out of reach - stand closer to it",
    "notWater": "the shard says that tile is not water - check WATER_LAND_GRAPHICS and "
                "WATER_STATIC_GRAPHICS",
    "mounted": "the shard says you are still mounted",
    "saving": "the world is saving - run it again in a moment",
    "throttled": "the shard says wait - run it again in a moment",
    "noCursor": "the pole raised no cursor",
    "unknown": "unreadable outcome, check OUTCOME_TEXT",
}


def pack_counts():
    return counts_by_graphic(pack_contents())


def pack_total(counts):
    return sum(counts.values())


# Measured off the pack rather than read off the journal: the line names the catch, the pack says
# what art it arrived as
def record_cast(recorder, skill, start, outcome, caught, before):
    if outcome == "caught":
        settled(CATCH_SETTLE, CATCH_POLL, lambda: pack_total(pack_counts()) > pack_total(before))

    gained, _lost = diff_counts(before, pack_counts())
    rows = [(caught, graphic, hue, quantity)
            for (graphic, hue), quantity in sorted(gained.items())]

    recorder.record(start, outcome, "fishing pole", gained=rows)
    settled(GAIN_SETTLE, GAIN_POLL, lambda: skill.read() != start)
    recorder.close(skill.last())


def fish():
    if API.HasTarget():
        API.CancelTarget()

    skill_name = find_skill_name(SKILL_NAMES)

    if skill_name is None:
        return "the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES)

    skill = SkillReader(skill_name)
    start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

    if start is None:
        return "%s is not reading yet - run it again once the skill list has arrived" % skill_name

    reason = first_reason([dead(), skill_capped(skill_name)])

    if reason is not None:
        return reason

    if not dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL):
        return "could not get off the mount"

    if GUARD_PHRASE:
        API.Msg(GUARD_PHRASE)

    pole = find_pole(POLE_GRAPHICS, POLE_NAME_WORDS, HAND_LAYERS, log)

    if pole is None:
        return "no fishing pole in hand or in the pack"

    tile = nearest_water(Terrain(), FISH_RANGE, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS)

    if tile is None:
        return "no water within %d tiles" % FISH_RANGE

    log("%s at %s, casting at %d,%d" % (skill_name, reading(start), tile["x"], tile["y"]))

    recorder = attempt_log(DATA_PATH, skill_name, log)
    before = pack_counts() if recorder.recording() else {}
    outcome, caught = Angler(OUTCOME_TEXT, CAST_CONFIG, log, log.stamp).cast_once(pole, tile)

    if outcome in ("caught", "failed") and recorder.recording():
        record_cast(recorder, skill, start, outcome, caught, before)

    if outcome == "caught":
        return "caught %s" % (caught or "something the journal did not name")

    if outcome == "unknown":
        for line in journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES, log.stamp):
            log("  " + line)

    return ENDINGS.get(outcome, outcome)


try:
    ending = fish()
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    ending = "threw - %s" % error

log(ending)
API.Stop()
