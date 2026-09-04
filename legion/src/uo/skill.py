import API


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

    def read(self):
        skill = API.GetSkill(self._name)

        if skill is None:
            return None

        value = skill.Value

        if value <= 0.0 and not self._seen:
            return None

        self._seen = True

        return value

    def name(self):
        skill = API.GetSkill(self._name)

        return skill.Name if skill is not None and skill.Name else self._name

    def cap(self):
        skill = API.GetSkill(self._name)

        return skill.Cap if skill is not None else None

    def wait(self, timeout, poll):
        waited = 0.0

        while True:
            value = self.read()

            if value is not None:
                return value

            if waited >= timeout:
                return None

            API.Pause(poll)
            waited += poll
