import logging

log = logging.getLogger(__name__)


class Line(object):
    _line: str

    def __init__(self):
        self._line = None

    def write(self, line):
        self._line = line

    def read(self):
        return self._line
