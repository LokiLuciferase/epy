#!/usr/bin/env python3
import subprocess
import shutil
import shlex
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pathlib import Path
from tempfile import TemporaryDirectory

from epy_reader import __version__


class FileCache:
    @staticmethod
    def _download_http(url: str, out: Path):
        header = {
            "User-Agent": f"epy/v{__version__}",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        }
        try:
            with urlopen(Request(url, headers=header)) as response:
                with open(out, "wb") as f:
                    f.write(response.read())
        except HTTPError as e:
            raise e
        except URLError as e:
            raise e

    @staticmethod
    def _download_ssh(url: str, out: Path) -> Path:
        if not shutil.which("scp"):
            raise RuntimeError("`scp` not found: cannot resolve SSH URL")
        parsed = urlparse(url)
        success = False
        errmsg = ""
        for path in (parsed.path, shlex.quote(parsed.path)):
            cmd = ["scp", "-Tq", f'{parsed.netloc}:{path}', f'{out.parent}/tmp']
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if run.returncode == 0:
                success = True
                break
            else:
                errmsg = run.stderr.decode("utf-8")
        if not success:
            raise RuntimeError(f"Failed to download {url}: {errmsg}")
        shutil.move(out.parent.joinpath("tmp"), str(out))

    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            self._cache_dir = TemporaryDirectory()
            self._cache_dir_path = Path(self._cache_dir.name)
        else:
            self.cache_dir = cache_dir

    def ensure_cached(self, path_or_url: str) -> str:
        parsed = urlparse(path_or_url)
        if not parsed.scheme:
            return str(Path(path_or_url).absolute())
        elif parsed.scheme == "file":
            return str(Path(parsed.path).absolute())
        else:
            out = self._cache_dir_path.joinpath(Path(parsed.path).name)
            if not out.exists():
                if parsed.scheme in ("http", "https"):
                    FileCache._download_http(path_or_url, out)
                elif parsed.scheme == "ssh":
                    FileCache._download_ssh(path_or_url, out)
                else:
                    raise RuntimeError(f"Unsupported URL scheme {parsed.scheme}")
            return str(out.resolve())
