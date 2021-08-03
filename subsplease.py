from __future__ import annotations

import difflib
from functools import partial
import logging
import os
import re
import tempfile
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import BinaryIO, Iterator, List, Union

from xdcc import XDCC, logger

logging.basicConfig(level=logging.INFO)
# logger.setLevel(logging.DEBUG)

BOTS = [
    "CR-HOLLAND|NEW",
    "CR-ARUTHA|NEW",
    "ARUTHA-BATCH|1080p",
    "ARUTHA-BATCH|720p",
    "ARUTHA-BATCH|SD",
    # "Ginpachi-Sensei",
    # "SubsPlease|NEW",
]


FILENAME_RE = r"(\[(\w+)\] (.+?)(?: - (.+?))? [\[\(](\w+)[\]\)].*\.\w+)"  # filename, group, title, ep, res
LISTFILE_RE = r"#(\d+) +(\d+)x +\[([\d\. ]+)(\w)] " + FILENAME_RE  # id, dl, size, size_u


class ListFile:
    id: int
    downloads: int
    size: int
    filename: str
    group: str
    title: str
    episode: str
    resolution: str

    def __init__(self, string: str, bot: str = '') -> None:
        self.raw = string

        match = re.match(LISTFILE_RE, string)
        if match is None:
            warnings.warn(f"Incorrect file format: {string!r}", Warning)
            return

        id, dl, size, size_u, filename, group, title, ep, res = match.groups("")
        self.id = int(id)
        self.downloads = int(dl)
        size = float(size) * {"B": 1, "K": 0x400, "M": 0x100000, "G": 0x40000000}[size_u]
        self.size = int(size)
        self.filename = filename
        self.group = group
        self.title = title
        self.episode = ep
        self.resolution = res
        
        self.bot = bot

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if k != "raw" and v)
        return f"{type(self).__name__}({args})"


class SubsPleaseXDCC(XDCC):
    """An XDCC client just for SubsPlease"""

    def __init__(self, bot: str) -> None:
        super().__init__(bot, "#subsplease")

    def _get_list_cache(self) -> str:
        """Get the filename of the file list cache"""
        directory = os.path.join(tempfile.gettempdir(), "xdcc_cache")
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, f"{self.bot.replace('|', '.')}.xdcc.txt")

    def list_files(self) -> List[ListFile]:
        """List all files that you can download"""
        filename = self._get_list_cache()
        if os.path.exists(filename) and time.time() - os.path.getmtime(filename) <= 86400 and os.path.getsize(filename) >= 0x1000:
            with open(filename) as file:
                data = file.read()
        else:
            stream = open(filename, "wb+")
            self.send("list", stream)
            stream.seek(0)
            data = stream.read().decode()
        # remember to strip the headers and footers
        return [ListFile(i, self.bot) for i in data.splitlines()[4:-2]]

    def download(self, file_id: int, stream: Union[str, BinaryIO] = None) -> None:
        """Download a single file by id"""
        if isinstance(stream, str):
            stream = open(stream, "wb")

        self.send(file_id, stream)

    def search(self, title: str, cutoff: float = 0.6) -> List[ListFile]:
        """Search all animes by name"""
        files = self.list_files()
        matches = set(difflib.get_close_matches(title, {i.title for i in files}, n=8, cutoff=cutoff))
        if matches:
            return [i for i in files if i.title in matches]
        return []


def list_files(bot: str) -> List[ListFile]:
    with SubsPleaseXDCC(bot) as client:
        return client.list_files()

def list_all_files() -> Iterator[ListFile]:
    with ThreadPoolExecutor() as e:
        for files in e.map(list_files, BOTS):
            yield from files

def search(bot: str, title: str, cutoff: float = 0.6) -> List[ListFile]:
    with SubsPleaseXDCC(bot) as client:
        return client.search(title, cutoff)

def search_all(title: str, cutoff: float = 0.6) -> Iterator[ListFile]:
    with ThreadPoolExecutor() as e:
        for files in e.map(partial(search, title=title, cutoff=cutoff), BOTS):
            yield from files
