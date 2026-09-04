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
