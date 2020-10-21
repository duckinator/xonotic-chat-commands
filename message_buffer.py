from threading import Lock
import time


class MessageBuffer:
    """
    Call .write() to shove unprocessed data in, call .readline() to get
    a line out.
    """

    def __init__(self, prefix=None, suffix=None):
        self.mutex = Lock()

        self.prefix = prefix or b"\xff\xff\xff\xffn"
        self.suffix = suffix or b"\n"

        if isinstance(self.prefix, str):
            self.prefix = self.prefix.encode()

        if isinstance(self.suffix, str):
            self.suffix = self.suffix.encode()

        self._data = b''
        self._lines = []

    def write(self, s):
        if isinstance(s, str):
            s = s.encode()

        with self.mutex:
            self._data += s

    def _process(self):
        with self.mutex:
            while self.prefix in self._data and self.suffix in self._data:
                line, self._data = self._data.split(self.suffix, 1)

                if self.prefix in line:
                    extra, line = line.split(self.prefix)
                else:
                    extra = None

                if extra:
                    print(f"[INVALID LINE] {extra!r}")

                self._lines.append(line.decode())

    def readline(self):
        while len(self._lines) == 0:
            self._process()
            time.sleep(0.1)

        with self.mutex:
            return self._lines.pop(0)


if __name__ == "__main__":
    buf = MessageBuffer()
    buf.write(b"\xff\xff\xff\xffnfoo bar baz\nasdf\xff\xff\xff\xffnmeep")
    buf.write(" moop\n")
    print(repr(buf.readline()))
    print(repr(buf.readline()))
