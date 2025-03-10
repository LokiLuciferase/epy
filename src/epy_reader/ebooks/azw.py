import contextlib
import os
import shutil
import tempfile
import zipfile

from epy_reader.ebooks.epub import Epub
from epy_reader.tools import unpack_kindle_book


class Azw(Epub):
    def __init__(self, fileepub):
        self.path: str = self.get_abspath(fileepub)
        self.tmpdir = tempfile.mkdtemp(prefix="epy-")
        basename, _ = os.path.splitext(os.path.basename(self.path))
        self.file = os.path.join(self.tmpdir, "mobi8", basename + ".epub")

    def initialize(self):
        with contextlib.redirect_stdout(None):
            unpack_kindle_book(self.ensure_cached(self.path), self.tmpdir, epubver="A", use_hd=True)
        Epub.initialize(self)

    def cleanup(self) -> None:
        shutil.rmtree(self.tmpdir)
        return
