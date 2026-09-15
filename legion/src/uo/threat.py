import API

from uo.alert import Launcher
from uo.entity import hex_of
from uo.journal import forget, matched_bucket
from uo.notoriety import HOSTILE


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
    def __init__(self, config, log, companion, friend_label, hold=None):
        self._config = config
        self._log = log
        self._companion = companion
        self._friend_label = friend_label
        self._hold = hold
        self._alert = Launcher(log)
        self._last_hits = 0
        self._last_companion_hits = 0
        self._in_episode = False
        self._trouble_seen = False
        self._alarm_left = 0

    # Consuming: the roam idle loop never clears the journal, so said() would re-arm this every poll
    def _ambushed(self):
        text = self._config["ambush_text"]
        return bool(text) and matched_bucket([("ambushed", text)]) is not None

    def _sound(self):
        if self._alarm_left > 0 and self._alert.play(self._config["ambush_alarm"]):
            self._alarm_left -= 1

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
            theirs = ", %s %d/%s" % (self._friend_label(friend), friend.Hits,
                                     friend.HitsMax or "?")

        return "%s, %s%s" % (who, mine, theirs)

    def look(self):
        if not self._config["watch"]:
            return

        hits = API.Player.Hits
        hurt = dropped(self._last_hits, hits)

        if hits > 0:
            self._last_hits = hits

        friend = self._companion()
        friend_hits = friend.Hits if friend is not None else 0
        friend_hurt = dropped(self._last_companion_hits, friend_hits)

        if friend_hits > 0:
            self._last_companion_hits = friend_hits

        hostile = hostiles_near(HOSTILE, self._config["range"])
        trouble = hostile is not None or hurt or friend_hurt

        if self._ambushed():
            self._in_episode = True
            self._trouble_seen = False
            self._alarm_left = self._config["ambush_repeats"] if self._config["ambush_alarm"] else 0
            self._log("ambushed - %s" % self._describe(hostile, friend))
            API.HeadMsg(self._config["ambush_warning"], API.Player.Serial,
                        self._config["ambush_hue"])

            for command in self._config["ambush_notices"]:
                self._alert.run(command)

            # The scan above is stale once the hold returns; the next look reads the fight afresh
            if self._hold is not None:
                self._hold.wait(self._sound)
                # The button means the player has judged it safe, so every ambush line from while
                # the gump was up is stale - including the hold's own log line, which the client
                # files in the journal and which carries the very phrase this watch waits on
                forget(self._config["ambush_text"])
                self._in_episode = False
                self._trouble_seen = False
                self._alarm_left = 0
                self._alert.stop()

                return

        if trouble:
            if not self._in_episode:
                self._in_episode = True
                self._log("trouble - %s" % self._describe(hostile, friend))

            self._trouble_seen = True
        # An ambush announces monsters that take a cycle to appear, so the alarm outlives an empty
        # scan until a fight has come and gone or the repeats run out
        elif self._in_episode and (self._trouble_seen or self._alarm_left == 0):
            self._in_episode = False
            self._trouble_seen = False
            self._alarm_left = 0
            self._alert.stop()
            self._log("clear")

        self._sound()
