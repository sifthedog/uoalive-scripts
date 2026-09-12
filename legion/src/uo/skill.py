import API


# A name the client does not carry throws on some builds rather than answering None
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            if API.StopRequested:
                raise

            continue

    return None


def reading(value):
    return "unknown" if value is None else "%.1f" % value


def skill_value(name):
    skill = API.GetSkill(name)

    return skill.Value if skill is not None else 0.0


# The client answers 0 until the server has sent the skill list, which is not the same as a skill
# that is genuinely at 0
def wait_for_skill(name, timeout, poll):
    waited = 0.0

    while waited < timeout:
        skill = API.GetSkill(name)

        if skill is not None and skill.Value > 0:
            return skill

        API.Pause(poll)
        waited += poll

    return API.GetSkill(name)


class SkillReader(object):
    """Value reads 0.0 before the skill list arrives, which is also a real skill value."""

    def __init__(self, name):
        self._name = name
        self._seen = False
        self._last = None

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True
        self._last = value

        return value

    # Once the stop button is pressed the client answers nothing, so the last row of a run would
    # end unknown; the latest reading that did arrive is never further off than that
    def last(self):
        value = self.read()

        return value if value is not None else self._last

    def name(self):
        skill = API.GetSkill(self._name)

        return skill.Name if skill is not None and skill.Name else self._name

    def cap(self):
        skill = API.GetSkill(self._name)

        return skill.Cap if skill is not None else None

    def wait(self, timeout, poll):
        waited = 0.0

        while not API.StopRequested:
            value = self.read()

            if value is not None:
                return value

            if waited >= timeout:
                return self._accept_zero()

            API.Pause(poll)
            waited += poll

        return None

    # A 0 the client still answers once the wait is over is a real 0, not an unsent skill list
    def _accept_zero(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        self._seen = True
        self._last = skill.Value

        return skill.Value
