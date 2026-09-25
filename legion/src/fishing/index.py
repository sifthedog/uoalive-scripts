import API

from fishing.angler import Angler
from fishing.config import (AMBUSH_ALARM, AMBUSH_HOLD, AMBUSH_HOLD_BUTTON, AMBUSH_HOLD_HUE,
                            AMBUSH_HOLD_POLL, AMBUSH_HOLD_TEXT, AMBUSH_HUE, AMBUSH_NOTICES,
                            AMBUSH_REPEATS, AMBUSH_TEXT, AMBUSH_WARNING, BOAT_STOPPED_HOLD,
                            BOAT_STOPPED_HOLD_TEXT, BOAT_STOPPED_HUE, BOAT_STOPPED_TEXT,
                            BOAT_STOPPED_WARNING, CAST_POLL, CAST_TIMEOUT, CATCH_MODE_DEFAULT,
                            CATCH_MODE_HUE, CATCH_MODE_OPTIONS, CATCH_MODE_TEXT, CATCH_POLL,
                            CATCH_SETTLE, CAUGHT_TEXT, CURSOR_POLL, CURSOR_TIMEOUT, DATA_PATH,
                            DISMOUNT_ATTEMPTS, DISMOUNT_POLL, DISMOUNT_TIMEOUT, DROP_OFFSETS,
                            GAIN_POLL, GAIN_SETTLE, GUARD_PHRASE, HAND_LAYERS, HEARTBEAT_EVERY,
                            JOURNAL_TAIL_LINES, JOURNAL_TAIL_SECONDS, JUNK_ITEMS, LAND_TILE_GRAPHIC,
                            LOG_EVERY, MAX_CYCLES, MAX_THROTTLED, MAX_UNKNOWN,
                            MAX_UNREADABLE_REPORTS, MOVE_DELAY, NO_CURSOR_READ, OUTCOME_TEXT,
                            PICK_TIMEOUT, POLE_GRAPHICS, POLE_NAME_WORDS, PROMPT_TEXT,
                            SAVE_DONE_TEXT, SAVE_POLL, SAVE_WAIT,
                            SAVING_TEXT, SKILL_NAMES, SKILL_POLL, SKILL_TIMEOUT, STEP_DELAY,
                            STOPPED, THREAT_RANGE, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX,
                            TILES_AHEAD_DEFAULT, TILES_AHEAD_HUE, TILES_AHEAD_POLL,
                            TILES_AHEAD_PROMPT_TEXT, TURN_DELAY, WATCH_FOR_TROUBLE,
                            WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS)
from fishing.direction import tile_ahead, turn_toward_water
from fishing.pole import find_pole
from fishing.prompt import StartPrompt
from uo.clock import now
from uo.entity import hex_of
from uo.guards import dead, first_reason, skill_capped, stopped
from uo.heartbeat import Heartbeat
from uo.hold import Hold
from uo.journal import journal_tail
from uo.log import make_log
from uo.loop import backoff_for
from uo.mount import dismount
from uo.pack import amount_of, counts_by_graphic, diff_counts, items_of, pack_contents
from uo.record import attempt_log
from uo.retry import settled
from uo.save import SaveWatch
from uo.skill import SkillReader, find_skill_name, reading
from uo.target import request_one
from uo.threat import ThreatWatch
from uo.vitals import position_and_weight

log = make_log("fishing")
heartbeat = Heartbeat(HEARTBEAT_EVERY, log, "casts", position_and_weight)

skill_name = find_skill_name(SKILL_NAMES)


def stop_reason():
    return first_reason([stopped(STOPPED), dead(), skill_capped(skill_name)])


saves = SaveWatch(SAVING_TEXT, SAVE_DONE_TEXT, SAVE_WAIT, SAVE_POLL, log, heartbeat, stop_reason)

# Hold.wait() calls heartbeat.reset() - the only reason this script keeps one at all
hold_ambush = Hold({
    "text": AMBUSH_HOLD_TEXT,
    "button": AMBUSH_HOLD_BUTTON,
    "hue": AMBUSH_HOLD_HUE,
    "poll": AMBUSH_HOLD_POLL,
}, log, stop_reason, heartbeat)

hold_boat_stopped = Hold({
    "text": BOAT_STOPPED_HOLD_TEXT,
    "button": AMBUSH_HOLD_BUTTON,
    "hue": BOAT_STOPPED_HUE,
    "poll": AMBUSH_HOLD_POLL,
}, log, stop_reason, heartbeat)

# No companion aboard: fishing has no pet to lose track of, so both watches take no-ops for it
threat_ambush = ThreatWatch({
    "watch": WATCH_FOR_TROUBLE,
    "range": THREAT_RANGE,
    "ambush_text": AMBUSH_TEXT,
    "ambush_alarm": AMBUSH_ALARM,
    "ambush_notices": AMBUSH_NOTICES,
    "ambush_warning": AMBUSH_WARNING,
    "ambush_hue": AMBUSH_HUE,
    "ambush_repeats": AMBUSH_REPEATS,
}, log, lambda: None, lambda friend: "", hold_ambush if AMBUSH_HOLD else None)

# The same mechanism as an ambush - sound, HeadMsg, notices, an optional hold - just a different
# trigger phrase and wording
threat_boat_stopped = ThreatWatch({
    "watch": WATCH_FOR_TROUBLE,
    "range": THREAT_RANGE,
    "ambush_text": BOAT_STOPPED_TEXT,
    "ambush_alarm": AMBUSH_ALARM,
    "ambush_notices": AMBUSH_NOTICES,
    "ambush_warning": BOAT_STOPPED_WARNING,
    "ambush_hue": BOAT_STOPPED_HUE,
    "ambush_repeats": AMBUSH_REPEATS,
}, log, lambda: None, lambda friend: "", hold_boat_stopped if BOAT_STOPPED_HOLD else None)

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


# x/y are an offset from your own position (confirmed off TazUO's own LegionAPI.cs), so (0, 0)
# already drops at your feet - one of the eight adjacent tiles is used instead so catches spread out
# rather than stack underfoot. Picked off the clock since the sandbox has no random module
def drop_junk(items):
    for item in items:
        x, y = DROP_OFFSETS[int(now() * 1000) % len(DROP_OFFSETS)]
        API.MoveItemOffset(item.Serial, amount_of(item), x, y, 0)


def move_junk(container, items):
    for item in items:
        API.MoveItem(item.Serial, container, amount_of(item))
        API.Pause(MOVE_DELAY)


skill = SkillReader(skill_name or SKILL_NAMES[0])
recorder = attempt_log(DATA_PATH if skill_name else "", skill.name(), log)

stop = None
start = None

if skill_name is None:
    stop = "the client reports none of %s - check SKILL_NAMES" % ", ".join(SKILL_NAMES)
else:
    start = skill.wait(SKILL_TIMEOUT, SKILL_POLL)

    if start is None:
        stop = "%s is not reading yet - run it again once the skill list has arrived" % skill_name

container = None

if stop is None:
    answers = StartPrompt({
        "tiles_text": TILES_AHEAD_PROMPT_TEXT,
        "tiles_default": TILES_AHEAD_DEFAULT,
        "tiles_hue": TILES_AHEAD_HUE,
        "catch_text": CATCH_MODE_TEXT,
        "catch_options": CATCH_MODE_OPTIONS,
        "catch_default": CATCH_MODE_DEFAULT,
        "catch_hue": CATCH_MODE_HUE,
        "poll": TILES_AHEAD_POLL,
    }, log, stop_reason).ask()
    tiles_ahead = answers["tiles_ahead"]
    catch_mode = answers["catch_mode"]
    log.enabled = answers["debug_logs"]

    if catch_mode == "container":
        log("target the container to move junk catches into - ESC keeps them in the pack instead")
        serial = request_one(PICK_TIMEOUT)

        if serial is not None and serial != API.Backpack:
            container = serial
            log("moving junk catches into %s" % hex_of(container))
        else:
            catch_mode = "keep"
            log("nothing picked - junk catches will stay in the pack")

    angler = Angler(OUTCOME_TEXT, CAST_CONFIG, log, log.stamp)
    log("%s at %s, aiming %d tiles ahead, junk catches: %s"
        % (skill_name, reading(start), tiles_ahead, catch_mode))

    # Said once, before the loop: the pets stay guarding, so this does not need repeating every cast
    if GUARD_PHRASE:
        API.Msg(GUARD_PHRASE)

tally = 0
fails = 0
unknown = 0
throttled = 0
reported = 0
cycle = 0
unreadable_reports = 0

try:
    while stop is None and cycle < MAX_CYCLES:
        cycle += 1
        stop = stop_reason()

        if stop is not None:
            break

        # A frozen shard reads as every failure below, so it is waited out before any of them
        if saves.is_saving():
            saves.wait_out()
            unknown = 0
            throttled = 0
            continue

        threat_ambush.look()
        threat_boat_stopped.look()

        # Asked every cycle, so a remount costs a single cycle instead of the rest of the run
        if not dismount(DISMOUNT_ATTEMPTS, DISMOUNT_TIMEOUT, DISMOUNT_POLL):
            stop = "could not get off the mount"
            break

        pole = find_pole(POLE_GRAPHICS, POLE_NAME_WORDS, HAND_LAYERS, log)

        if pole is None:
            stop = "no fishing pole in hand or in the pack"
            break

        turn_toward_water(tiles_ahead, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS, TURN_DELAY)
        tile = tile_ahead(tiles_ahead, WATER_LAND_GRAPHICS, WATER_STATIC_GRAPHICS,
                         LAND_TILE_GRAPHIC)
        log("casting at %d,%d,%d (graphic %s, %s), standing at %d,%d, facing %s"
            % (tile["x"], tile["y"], tile["z"], hex_of(tile["graphic"]), tile["source"],
               API.Player.X, API.Player.Y, API.Player.Direction))
        # Swept off the pack rather than read off the catch line: the shard names species, and a
        # fish that lands after the read timed out is still here next cycle
        junk = items_of(JUNK_ITEMS) if catch_mode != "keep" else []

        if junk:
            log("%d junk in the pack" % len(junk))

            if catch_mode == "discard":
                drop_junk(junk)
            else:
                move_junk(container, junk)

        value = skill.read()
        before = pack_counts()
        outcome, caught = angler.cast_once(pole, tile)

        if outcome in ("caught", "failed") and recorder.recording():
            record_cast(recorder, skill, value, outcome, caught, before)

        if outcome == "caught":
            tally += 1
            unknown = 0
            throttled = 0
            unreadable_reports = 0
            log("caught %s" % (caught or "something the journal did not name"))
        elif outcome == "failed":
            tally += 1
            fails += 1
            unknown = 0
            throttled = 0
        elif outcome == "saving":
            saves.wait_out()
            unknown = 0
            throttled = 0
        elif outcome == "throttled":
            throttled += 1
            unknown = 0
            log("shard says wait (%d/%d), backing off" % (throttled, MAX_THROTTLED))
            API.Pause(backoff_for(throttled, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

            if throttled >= MAX_THROTTLED:
                stop = "the shard kept refusing the cast"
                break
        elif outcome in ("empty", "tooFar", "notWater", "mounted", "busy"):
            unknown = 0
        # An unreadable outcome does not stop the run - only noCursor counts toward MAX_UNKNOWN. A
        # short CAST_TIMEOUT hits this often as a matter of course, so the journal dump is capped
        # rather than printed every time - MAX_UNREADABLE_REPORTS resets once a catch lands clean
        elif outcome == "unknown":
            if unreadable_reports < MAX_UNREADABLE_REPORTS:
                unreadable_reports += 1
                log("unreadable outcome (%d/%d shown), check OUTCOME_TEXT"
                    % (unreadable_reports, MAX_UNREADABLE_REPORTS))

                for line in journal_tail(JOURNAL_TAIL_SECONDS, JOURNAL_TAIL_LINES, log.stamp):
                    log("  " + line)
        # noCursor: the pole raised no cursor and the shard said nothing either
        else:
            unknown += 1
            log("no target cursor (%d/%d), backing off" % (unknown, MAX_UNKNOWN))
            API.Pause(backoff_for(unknown, THROTTLE_BACKOFF, THROTTLE_BACKOFF_MAX))

        if unknown >= MAX_UNKNOWN:
            stop = "%d unreadable outcomes in a row" % MAX_UNKNOWN
            break

        if tally >= reported + LOG_EVERY:
            reported = tally
            log("%d casts, %d caught, %d failed" % (tally, tally - fails, fails))

        API.Pause(STEP_DELAY)
except Exception as error:
    # The stop button lands here as well, and the client waits for it to unwind the thread
    if API.StopRequested:
        raise

    if stop is None:
        stop = "threw - %s" % error
finally:
    recorder.close(skill.last())

if API.Pathfinding():
    API.CancelPathfinding()

reason = stop or "hit the %d working cycle backstop" % MAX_CYCLES

log("%d casts, %d caught, %d failed" % (tally, tally - fails, fails))
log("stopping - %s" % reason)
API.Stop()
