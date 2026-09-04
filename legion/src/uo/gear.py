import API


# Either hand: a katana is one-handed and a no-dachi two-handed, and meditation is refused while
# anything at all is held
def in_hand():
    return API.FindLayer("onehanded") or API.FindLayer("twohanded")
