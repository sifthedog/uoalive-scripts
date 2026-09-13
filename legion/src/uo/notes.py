from uo.clock import time_text
from uo.journal import journal_report
from uo.paths import append_line, beside_script
from uo.text import spoken, untagged


class NoteLog(object):
    """One block per report, appended to a file beside the script."""

    def __init__(self, path, log, append=None):
        self._path = path or ""
        self._log = log
        self._append = append if append is not None else append_line
        self._off = not self._path
        self._said = False

    def writing(self):
        return not self._off

    def where(self):
        return self._path

    def write(self, heading, rows):
        if self._off:
            return

        out = ["[%s] %s" % (time_text(), heading)]

        for label, values in rows:
            out.append("  %s:" % label)

            for value in values or ["(nothing)"]:
                out.append("    %s" % value)

        self._put("\n".join(out))

    # A run that cannot write its notes is still a run: the sink retires itself and says so once
    def _put(self, block):
        try:
            self._append(self._path, block)
        except Exception as error:
            self._off = True

            if not self._said:
                self._said = True
                self._log("cannot write %s (%s) - not writing notes this run"
                          % (self._path, error))


def note_log(path, log):
    return NoteLog(beside_script(path), log)


class Reporter(object):
    """What a craft could not read: a short line in the window, the whole of it in the notes.

    The window quotes the gump from the shard's own sentence on: the header before it and the rows
    after it are the same boilerplate every time.
    """

    def __init__(self, lines_of, config, log, notes=None, stamp=None):
        self._lines_of = lines_of
        self._config = config
        self._log = log
        self._notes = notes
        self._stamp = stamp
        self._said = 0
        self._said_where = False

    def forget(self):
        self._said = 0

    # extra is (label, sentence) pairs: the window says the sentence, the notes file labels it
    def say(self, why, gump, extra=None):
        text = untagged(" ".join(self._lines_of(gump))) if gump else ""
        rest = list(extra or [])

        self._write(why, text, rest)

        if self._said >= self._config["max_reports"]:
            return

        self._said += 1
        lines = journal_report(self._config["tail_seconds"], self._config["tail_lines"],
                               self._stamp)

        self._log("%s - the gump says '%s'"
                  % (why, spoken(text, "you", self._config["text_limit"]) or "(nothing)"))
        self._log("the journal says '%s'" % (" | ".join(lines) or "(nothing)"))

        for _label, sentence in rest:
            self._log(sentence)

        self._say_where()

    # Said when there is something to read rather than at startup, where the form has not yet told
    # the run whether it wants any logs at all
    def _say_where(self):
        if self._notes is None or not self._notes.writing() or self._said_where:
            return

        self._said_where = True
        self._log("the whole of it is in %s" % self._notes.where())

    # Uncapped, and untruncated: the window's two reports are a pointer, the file is the evidence
    def _write(self, why, text, rest):
        if self._notes is None or not self._notes.writing():
            return

        rows = [("gump", [text] if text else []),
                ("journal", journal_report(self._config["notes_seconds"], None, self._stamp,
                                           False))]

        self._notes.write(why, rows + [(label, [sentence]) for label, sentence in rest])
