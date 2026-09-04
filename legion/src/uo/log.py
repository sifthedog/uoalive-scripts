import API


def make_log(prefix):
    def log(message):
        API.SysMsg(prefix + ": " + message)

    return log
