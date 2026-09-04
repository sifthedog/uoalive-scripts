import API

from uo.clock import now
from uo.entity import hex_of
from uo.journal import read_outcome, said
from uo.notoriety import CALL_ON_SIGHT, HOSTILE


# 0 is what the client reports while it is refreshing stats, and for a mobile it has lost track of,
# so a fall to 0 is no news at all
def dropped(was, is_now):
    return was > 0 and is_now > 0 and is_now < was


def hostiles_near(notoriety, within):
    found = API.GetAllMobiles(None, within, notoriety) or []

    for mobile in found:
        # IsRenamable is how the rest of this repo tells your own pet from a stranger's, and a pet
        # flagged gray by whatever it was fighting would otherwise read as the thing attacking you
        if mobile.Serial != API.Player.Serial and not mobile.IsDead and not mobile.IsRenamable:
            return mobile

    return None


class ThreatWatch(object):
    def __init__(self, config, log, companion, friend_noun):
        self._config = config
        self._log = log
        self._companion = companion
        self._friend_noun = friend_noun
        self._last_hits = 0
        self._last_companion_hits = 0
        self._last_call = 0.0
        self._calls = 0
        self._in_episode = False
        self._no_guards = False
        self._said_protection = False
        self._zone = None

    def _read_zone(self):
        if said(self._config["zone_text"]):
            self._zone = "guarded"
        elif said(self._config["unguarded_text"]):
            self._zone = "unguarded"

    # Nothing in the API answers this. A yellow human is a guard or a vendor, and either one means a
    # town, which is the best the client can be asked.
    def _protection(self):
        if self._zone is not None:
            return "the journal says %s" % self._zone

        seen = API.GetAllMobiles(None, self._config["range"], [API.Notoriety.Invulnerable]) or []

        for mobile in seen:
            if mobile.IsHuman and not mobile.IsDead:
                return "an invulnerable '%s' in sight, so probably a town" % (mobile.Name or "?")

        return "nothing in sight to say either way"

    def _call_guards(self):
        limit = self._config["calls"]

        if self._no_guards or (limit > 0 and self._calls >= limit):
            return

        at = now()

        if self._calls > 0 and at - self._last_call < self._config["call_delay"]:
            return

        self._last_call = at
        self._calls += 1

        if not self._said_protection:
            self._said_protection = True
            self._log("guard protection - %s" % self._protection())

        self._log("calling the guards (%d%s)" % (self._calls, "/%d" % limit if limit > 0 else ""))
        API.Msg(self._config["call"])

        refusals = self._config["no_guards_text"]

        if not refusals:
            return

        wait = self._config["reply_wait"]

        if read_outcome([("refused", refusals)], wait, wait) is not None:
            self._no_guards = True
            self._log("the shard says the guards cannot be called here - not calling again this run")

    def _describe(self, hostile, friend):
        if hostile is not None:
            who = "'%s' %s %d tiles off" % (
                hostile.Name or "?",
                hex_of(hostile.Graphic),
                hostile.Distance,
            )
        else:
            who = "nothing in sight"

        ceiling = API.Player.HitsMax
        mine = "you %d/%s" % (API.Player.Hits, ceiling if ceiling > 0 else "?")
        theirs = ""

        if friend is not None:
            theirs = ", %s %d/%s" % (self._friend_noun, friend.Hits, friend.HitsMax or "?")

        return "%s, %s%s" % (who, mine, theirs)

    def look(self):
        if not self._config["watch"]:
            return

        self._read_zone()

        hits = API.Player.Hits
        hurt = dropped(self._last_hits, hits)

        if hits > 0:
            self._last_hits = hits

        friend = self._companion()
        friend_hits = friend.Hits if friend is not None else 0
        friend_hurt = dropped(self._last_companion_hits, friend_hits)

        if friend_hits > 0:
            self._last_companion_hits = friend_hits

        attack_text = self._config["attack_text"]
        attacked = said(attack_text) if attack_text else False
        hostile = hostiles_near(HOSTILE, self._config["range"])

        if hostile is None and not hurt and not friend_hurt and not attacked:
            if self._in_episode:
                self._in_episode = False
                self._calls = 0
                self._log("clear")

            return

        if not self._in_episode:
            self._in_episode = True
            self._log("trouble - %s" % self._describe(hostile, friend))

        # Blood drawn is evidence whatever its notoriety; being in sight is only evidence for the
        # notorieties CALL_ON_SIGHT names
        on_sight = hostile is not None and hostile.Notoriety in CALL_ON_SIGHT

        if hurt or friend_hurt or attacked or on_sight:
            self._call_guards()
