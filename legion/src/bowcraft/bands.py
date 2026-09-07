# Ceilings are exclusive
def band_for(bands, value):
    if value is None:
        return None

    for ceiling, product in bands:
        if ceiling is None or value < ceiling:
            return product

    return None
