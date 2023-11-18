from __future__ import annotations

import io
import logging
import random
import shlex
import threading
import time
import warnings
from typing import Any, BinaryIO, Generic, Optional, TypeVar, overload

import irc.client
from tqdm import tqdm

irc.client.ServerConnection.buffer_class.encoding = "latin-1"
logger = logging.getLogger(__name__)
BinaryIOType = TypeVar("BinaryIOType", bound=BinaryIO)


class XDCCFile(Generic[BinaryIOType]):
    """An object representing an XDCC file, this is purely for download abstraction"""

    filename: str
    size: int
    stream: BinaryIOType

    def __init__(self, filename: str, size: int, stream: BinaryIOType = None):
        self.filename = filename
        self.size = size
        self.stream = stream or io.BytesIO()
        self._tqdm = tqdm(
            desc=self.filename, total=self.size, unit="B", unit_scale=True
        )

    def _write(self, data: bytes) -> None:
        self.stream.write(data)
        self._tqdm.update(len(data))
        if self._download_complete:
            self._tqdm.close()

    @property
    def _download_complete(self) -> bool:
        return self._tqdm.n >= self._tqdm.total  # type: ignore

    def __str__(self) -> str:
        f"<XDCC File \"{self.filename!r}\" ({self.size}B) {'COMPLETED' if self._download_complete else 'DOWNLOADING'}>"


class XDCC(irc.client.SimpleIRCClient):
    """An abstraction of the XDCC protocol

    The protocol is abstracted as to be thread-safe (just blocking) and have a system of requests and responses.

    Usage:
    >>> # get list of files
    >>> with XDCC("<botname>") as client:
    >>>     file = client.send("list")
    >>>     print(f"Open {file.filename} for a list of files")

    >>> # download file
    >>> with XDCC("<botname>") as client:
    >>>     client.send(1234)
    """

    bot: str
    channel: Optional[str]
    _file: Optional[XDCCFile[Any]] = None
    __stream: Optional[BinaryIO] = None

    connected: bool = True

    def __init__(self, bot: str, channel: Optional[str] = None):
        """Construct an XDCC Client

        Takes in a pack or list of packs to request, this will be requested one by one and finally all returned at once.

        """
        super().__init__()

        self.bot = bot
        self.channel = channel

        # avalible_lock is for whether it's possible to download a file
        # dl_lock is for whether the file has been downloaded
        self.avalible_lock = threading.Lock()
        self.avalible_lock.acquire()
        self.dl_lock = threading.Lock()

    def on_ctcp(self, connection, event):
        """The only possible ctcp event we want is a dcc one caused by a send command

        In that case we create a new file object and open a dcc connection to download the file.
        If a download is currently happening we simply ignore the event
        """
        if event.arguments[0] != "DCC":
            return

        payload = event.arguments[1]
        command, filename, peer_address, peer_port, size = shlex.split(payload)
        if command != "SEND" or self.dl_lock.locked():
            return

        self.dl_lock.acquire()
        logger.debug(f"{self.bot}: CTCP {payload!r}")

        if self.__stream is None or self.__stream.closed:
            stream = open(filename, "wb")
        else:
            stream = self.__stream

        self.file: XDCCFile[Any] = XDCCFile(filename, int(size), stream)

        try:
            peer_address = irc.client.ip_numstr_to_quad(peer_address)
            peer_port = int(peer_port)
            self.dcc_connection = self.dcc_connect(peer_address, peer_port, "raw")
        except Exception as e:
            self.dl_lock.release()
            warnings.warn(f"Cannot connect to bot, got invalid ip: {e}", Warning)
            return

    def on_dccmsg(self, connection, event):
        """Receive a DCC msg block from the bot and write it to the current file

        If the download is completed disconnect the connection and release the dl lock
        """
        if self.file is None:
            raise Exception("Recieved data when there's no file to output to")

        data = event.arguments[0]
        self.file._write(data)

        if self.file._download_complete:
            self.dcc_connection.disconnect()

    def on_dcc_disconnect(self, c, e):
        """When a connection is closed by the bot or by us end the download by releasing the dl lock"""
        self.dl_lock.release()

    def on_welcome(self, c, e):
        logger.debug(f"{self.bot}: WELCOME")
        if self.channel:
            self.connection.join(self.channel)
        else:
            self.avalible_lock.release()

    def on_join(self, c, e):
        logger.debug(f"{self.bot}: JOIN")
        self.avalible_lock.release()

    @overload
    def send(self, pack: Any, stream: None = None) -> XDCCFile[io.BufferedWriter]:
        ...

    @overload
    def send(self, pack: Any, stream: BinaryIOType) -> XDCCFile[BinaryIOType]:
        ...

    def send(self, pack: Any, stream: Optional[BinaryIO] = None, timeout: float = -1):
        """Send a pack to the bot, this will pause the main thread and wait until it has been downloaded"""
        # wait until avalible and then lock
        self.avalible_lock.acquire(timeout=60)
        self.__stream = stream

        logger.debug(f"{self.bot}: SEND {pack!r}")
        self.connection.ctcp("xdcc", self.bot, "send " + str(pack))
        # wait until dl is complete and unlock
        time.sleep(3)
        success = self.dl_lock.acquire(timeout=timeout)
        if not success:
            raise Exception("Send request timeout out")
        self.dl_lock.release()

        return self.file

    def connect(
        self, server: str = "irc.rizon.net", port: int = 6670, nickname: str = None
    ):
        """Connects to the icp server"""
        nickname = nickname or "".join(random.choices("anonymous", k=9))

        self.connection.connect(server, port, nickname)

    def _run_until_disconnect(self):
        while self.connected:
            self.reactor.process_once(0.2)  # .2 is default

    def start(self):
        """Starts the xdcc client, quits once the connections is closed"""
        if not self.connection.connected:
            self.connect()

        t = threading.Thread(target=self._run_until_disconnect)
        t.start()
        return t

    def close(self):
        """Close the client"""
        self.connected = False
        if self.connection.connected:
            self.connection.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        self.close()
