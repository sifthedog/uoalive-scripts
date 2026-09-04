import API

from uo.retry import settled


def dismount(attempts, timeout, poll):
    if not API.Player.IsMounted:
        return True

    for _attempt in range(attempts):
        API.Dismount()

        if settled(timeout, poll, lambda: not API.Player.IsMounted):
            return True

    return False
