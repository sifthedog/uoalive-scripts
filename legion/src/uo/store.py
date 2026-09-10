import json


class Store(object):
    """A JSON Lines file, read whole and appended a row at a time."""

    def __init__(self, path, log):
        self._path = path or ""
        self._log = log
        self._complained = False

    def on(self):
        return bool(self._path)

    def path(self):
        return self._path

    def _complain(self, verb, error):
        if self._complained:
            return

        self._complained = True
        self._log("could not %s %s (%s), carrying on without it" % (verb, self._path, error))

    # A missing file is the first run, so it is not worth a line
    def load(self):
        if not self._path:
            return []

        try:
            handle = open(self._path, "r")
        except (IOError, OSError):
            return []

        rows = []
        broken = 0

        try:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                try:
                    row = json.loads(line)
                except ValueError:
                    broken += 1
                    continue

                if isinstance(row, dict):
                    rows.append(row)
                else:
                    broken += 1
        finally:
            handle.close()

        if broken:
            self._log("%d unreadable line(s) in %s skipped" % (broken, self._path))

        return rows

    def _write(self, mode, rows):
        if not self._path:
            return

        # A row the encoder refuses is a bug in the caller, not a reason to end the run
        try:
            handle = open(self._path, mode)

            try:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
            finally:
                handle.close()
        except (IOError, OSError, TypeError, ValueError) as error:
            self._complain("write", error)

    def append(self, rows):
        if rows:
            self._write("a", rows)

    def rewrite(self, rows):
        self._write("w", rows)
