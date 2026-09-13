def words_of(text):
    letters = []

    for char in (text or "").lower():
        letters.append(char if char.isalnum() else " ")

    return "".join(letters).split()


def word_in(text, words):
    found = words_of(text)

    for word in words:
        if word in found:
            return True

    return False


def phrase_in(text, phrase):
    found = words_of(text)
    wanted = words_of(phrase)

    for start in range(len(found) - len(wanted) + 1):
        if found[start:start + len(wanted)] == wanted:
            return True

    return len(wanted) == 0


def any_in(text, fragments):
    low = (text or "").lower()

    for fragment in fragments:
        if fragment in low:
            return True

    return False


def untagged(text):
    kept = []
    inside = False

    for char in text or "":
        if char == "<":
            inside = True
        elif char == ">":
            inside = False
        elif not inside:
            kept.append(char)

    return "".join(kept)


def clipped(text, limit):
    flat = " ".join((text or "").split())

    return flat if len(flat) <= limit else flat[:limit] + "..."


# A craft gump is a header, then a notice, then every row it can make: the sentence talking to you
# sits in the middle, where neither end of a clip reaches it
def spoken(text, word, limit):
    flat = " ".join((text or "").split())
    at = flat.lower().find(word.lower())

    if at <= 0:
        return clipped(flat, limit)

    return "..." + clipped(flat[at:], limit)
