import API


# GetSkill answers None for a name it does not know, and a name the client does not carry throws
# rather than answering None on some builds
def find_skill_name(names):
    for name in names:
        try:
            if API.GetSkill(name) is not None:
                return name
        except Exception:
            continue

    return None


# The first row whose ceiling the value is under wins, so the ceilings are exclusive
def band_for(bands, value):
    if value is None:
        return None

    for ceiling, product in bands:
        if ceiling is None or value < ceiling:
            return product

    return None
