import argparse
import logging
from contextlib import suppress
from typing import NoReturn

import serial

from space_collector.network.client import Client


class PlayerGameClient(Client):
    def __init__(
        self, server_addr: str, port: int, serial_port_name: str, team_name: str
    ) -> None:
        logging.basicConfig(
            filename=f"client_{team_name.replace(' ', '_')}.log",
            level=logging.INFO,
            format=(
                "%(asctime)s [%(levelname)-8s] %(filename)20s(%(lineno)3s):%(funcName)-20s :: "
                "%(message)s"
            ),
            datefmt="%m/%d/%Y %H:%M:%S",
        )
        logger = logging.getLogger()
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(console_handler)

        super().__init__(server_addr, port, team_name, spectator=False)
        logging.info("opening %s", serial_port_name)
        self.serial_port = serial.Serial(serial_port_name, 115200, timeout=1)
        logging.info("port opened")

    def run(self) -> NoReturn:
        logging.info(self.readline(timeout=3600))
        self.serial_write("START\n")
        while True:
            with suppress(serial.SerialTimeoutException):
                command = self.serial_read().strip()
                if command:
                    response = self.send_command(command)
                    self.serial_write(response)

    def send_command(self, command: str) -> str:
        if not command.endswith("\n"):
            command += "\n"
        logging.info("Command TCP: %s", command.strip())
        self.send(command)
        response = self.readline() + "\n"
        logging.info("Response TCP: %s", response.strip())
        return response

    def serial_write(self, text: str) -> None:
        logging.info("serial write: %s", text)
        self.serial_port.write(text.encode("utf-8"))
        self.serial_port.flush()

    def serial_read(self) -> str:
        read = self.serial_port.readline()
        logging.info("serial read: %s", str(read))
        return read.decode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game client.")
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        help="name of server on the network",
        default="localhost",
    )
    parser.add_argument(
        "-p", "--port", type=int, help="location where server listens", default=16210
    )
    parser.add_argument(
        "-s",
        "--serial",
        type=str,
        help="serial port (115200 8N1)",
        default="/dev/ttyUSB0",
    )
    parser.add_argument(
        "-n", "--team-name", type=str, help="team name", default="Default team name"
    )
    args = parser.parse_args()

    PlayerGameClient(args.address, args.port, args.serial, args.team_name).run()
