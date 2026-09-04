import API

# Throwaway diagnostic for magery.py: casts Bless three ways and says which one the shard took.
# Delete it once the answer is known.

SPELL = "Bless"
BUFF = "Bless"

WATCH = 6.0
POLL = 0.2

# Between passes, so the shard's action throttle is not what answers the question
BETWEEN = 3.0

ANSWER_WAIT = 1.5


def log(message):
    API.SysMsg("probe: " + message)


def buff_up():
    for buff in API.ActiveBuffs() or []:
        if str(buff.Type) == BUFF:
            return True

    return False


def cursor_flags():
    seen = []

    for kind in ["any", "beneficial", "neutral", "harmful"]:
        try:
            if API.HasTarget(kind):
                seen.append(kind)
        except Exception as error:
            seen.append("%s threw" % kind)

    return seen


def clear():
    if API.HasTarget():
        API.CancelTarget()

    API.CancelPreTarget()
    API.Pause(BETWEEN)


# Reports the first moment a cursor is seen and what the shard did, without answering anything
def watch(label, answer):
    mana_before = API.Player.Mana
    up_before = buff_up()

    waited = 0.0
    said_cursor = False
    said_casting = False
    answered = None

    while waited < WATCH:
        if API.Player.IsCasting and not said_casting:
            said_casting = True
            log("%s: IsCasting went true at %.1fs" % (label, waited))

        flags = cursor_flags()

        if flags and not said_cursor:
            said_cursor = True
            log("%s: cursor seen at %.1fs as %s" % (label, waited, "/".join(flags)))

            if answer:
                answered = try_answers(label)

        if API.Player.Mana < mana_before:
            log("%s: mana fell %d -> %d at %.1fs" % (label, mana_before, API.Player.Mana, waited))
            break

        API.Pause(POLL)
        waited += POLL

    if not said_cursor:
        log("%s: no cursor ever reported by HasTarget" % label)

    if not said_casting:
        log("%s: IsCasting never went true - the client does not publish it" % label)

    log(
        "%s: done - mana %d -> %d, buff %s -> %s, answered by %s"
        % (
            label,
            mana_before,
            API.Player.Mana,
            up_before,
            buff_up(),
            answered or "nothing",
        )
    )


def try_answers(label):
    for how in ["Target(player)", "TargetSelf", "Target(serial)"]:
        try:
            if how == "Target(player)":
                API.Target(API.Player)
            elif how == "TargetSelf":
                API.TargetSelf()
            else:
                API.Target(API.Player.Serial)
        except Exception as error:
            log("%s: %s threw - %s" % (label, how, error))
            continue

        waited = 0.0

        while waited < ANSWER_WAIT:
            API.Pause(POLL)
            waited += POLL

            if not API.HasTarget():
                log("%s: %s brought the cursor down" % (label, how))

                return how

        log("%s: %s did nothing" % (label, how))

    return None


log("serial %s, %d/%d mana, three casts of %s coming" % (
    hex(API.Player.Serial), API.Player.Mana, API.Player.ManaMax, SPELL))

clear()

log("pass 1: PreTarget beneficial, then cast")
API.PreTarget(API.Player.Serial, "beneficial")
API.CastSpell(SPELL)
watch("beneficial", False)

clear()

log("pass 2: PreTarget neutral, then cast")
API.PreTarget(API.Player.Serial, "neutral")
API.CastSpell(SPELL)
watch("neutral", False)

clear()

log("pass 3: no pre-target, answer the cursor when it appears")
API.CastSpell(SPELL)
watch("after", True)

clear()

log("done - paste the lines above back")
API.Stop()
