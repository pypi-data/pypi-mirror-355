from __future__ import annotations

import json
import logging
from contextlib import suppress
from socket import socket
from threading import Lock, Thread
from time import perf_counter, sleep

DEFAULT_TIMEOUT = 20  # seconds


class NetworkError(Exception):
    pass


class DataHandler:
    BUFSIZ = 1024

    def _receive_data(self) -> None:
        while True:
            try:
                data = self.socket.recv(self.BUFSIZ)
            except TimeoutError:
                continue  # same player try again
            except OSError:
                return
            with self._input_lock:
                self._inputbytes += data
                try:
                    self._input += self._inputbytes.decode("utf-8")
                    self._inputbytes = b""
                except UnicodeDecodeError:
                    pass

    def __init__(self, socket_: socket) -> None:
        self._inputbytes = b""
        self._input = ""
        self._input_lock = Lock()
        self.socket = socket_
        self.socket.settimeout(0.01)

        receive_thread = Thread(target=self._receive_data, args=(), daemon=True)
        receive_thread.start()

    def input_empty(self) -> bool:
        return "\n" not in self._input

    def readline(self: DataHandler, timeout: int = DEFAULT_TIMEOUT) -> str:
        start = perf_counter()
        while "\n" not in self._input:
            if perf_counter() - start > timeout:
                logging.debug("timeout")
                raise NetworkError
            sleep(0.005)
        with self._input_lock:
            index = self._input.index("\n")
            line = self._input[:index]
            self._input = self._input[index + 1 :]
            return line

    def read_json(self: DataHandler, timeout: int = DEFAULT_TIMEOUT) -> object:
        start = perf_counter()
        logging.debug("read_json")
        json_text = ""
        while True:
            json_text += "\n" + self.readline(timeout)
            with suppress(json.JSONDecodeError):
                return json.loads(json_text)
            if perf_counter() - start > timeout:
                logging.debug("timeout")
                raise NetworkError

    def write(self: DataHandler, message: str) -> None:
        logging.debug("write %s", message[:100])
        try:
            self.socket.send(bytes(message, "utf8"))
        except BrokenPipeError as exc:
            raise NetworkError from exc

    def write_json(self, data: object) -> None:
        self.write(json.dumps(data) + "\n")
