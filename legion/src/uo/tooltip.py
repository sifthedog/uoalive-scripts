"""An item's tooltip lines, read into a name, a tier, durability, weight and a property map.

Pure text: nothing here asks the client. Every rule is a string method because `re` is not in the
bundle. A line no rule understands is still kept, as a flag, so the map never loses one.
"""


# "15%" -> 15, "+20%" -> 20, "-10" -> -10, "2.5s" -> 2.5; anything else -> None
def tooltip_number(token):
    text = token.strip().rstrip("%")

    if len(text) > 1 and text.endswith("s") and text[-2].isdigit():
        text = text[:-1]

    if text.startswith("+") or text.startswith("-"):
        sign = -1 if text[0] == "-" else 1
        text = text[1:]
    else:
        sign = 1

    if not text or text.count(".") > 1 or not text.replace(".", "").isdigit():
        return None

    if "." in text:
        return sign * float(text)

    return sign * int(text)


def tooltip_key(tokens):
    return " ".join(tokens).strip().rstrip(":").strip()


def _numbers_in(text):
    found = []

    for token in text.replace(":", " ").replace("/", " ").split():
        number = tooltip_number(token)

        if number is not None:
            found.append(number)

    return found


def _starts_with_any(low, words):
    for word in words:
        if low.startswith(word.lower()):
            return word.lower()

    return None


def _tier_of(low, line, tiers):
    for tier in tiers:
        if low == tier.lower():
            return line

    return None


# A trailing number, and the two-number range before it: `weapon damage 13 - 15`
def _numbered(tokens):
    for index in range(len(tokens) - 1, -1, -1):
        number = tooltip_number(tokens[index])

        if number is None:
            continue

        if index >= 2 and tokens[index - 1] == "-":
            low = tooltip_number(tokens[index - 2])

            if low is not None:
                return tooltip_key(tokens[:index - 2]), [low, number]

        return tooltip_key(tokens[:index]), number

    return None, None


def parse_tooltip(lines, config):
    kept = [line.strip() for line in lines if line and line.strip()]
    parsed = {"name": kept[0] if kept else "", "tier": None, "durability": None, "weight": None,
              "props": {}}
    props = parsed["props"]

    for line in kept[1:]:
        low = line.lower()
        tier = _tier_of(low, line, config["tier"])

        if tier is not None:
            parsed["tier"] = tier
            continue

        word = _starts_with_any(low, config["durability"])

        if word is not None:
            numbers = _numbers_in(low[len(word):])

            if len(numbers) >= 2:
                parsed["durability"] = {"current": numbers[0], "max": numbers[1]}
                continue

        word = _starts_with_any(low, config["weight"])

        if word is not None:
            numbers = _numbers_in(low[len(word):])

            if numbers:
                parsed["weight"] = numbers[0]
                continue

        prefix = _starts_with_any(low, config["prefixes"])

        if prefix is not None:
            props[prefix] = line[len(prefix):].strip()
            continue

        key, value = _numbered(low.split())

        if key:
            props[key] = value
            continue

        if ":" in line:
            before, after = line.split(":", 1)
            props[tooltip_key(before.lower().split())] = after.strip()
            continue

        props[low] = True

    return parsed
