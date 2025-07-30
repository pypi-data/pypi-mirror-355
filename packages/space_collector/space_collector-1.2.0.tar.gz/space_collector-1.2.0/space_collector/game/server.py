import argparse
import contextlib
import json
import logging
import sys
from time import perf_counter, sleep

from space_collector.game.constants import MAX_GAME_DURATION
from space_collector.game.game import Game
from space_collector.network.data_handler import NetworkError
from space_collector.network.server import ClientData, Server

MAX_NB_PLAYERS = 4
server_connection_timeout = 10


class GameServer(Server):
    def __init__(self: "GameServer", host: str, port: int) -> None:
        super().__init__(host, port)
        self.game = Game()
        self._wait_connections()
        for player in self.players:
            self.game.add_player(player.name)

    @property
    def players(self) -> list[ClientData]:
        return [client for client in list(self.clients) if not client.spectator]

    @property
    def spectators(self) -> list[ClientData]:
        return [client for client in list(self.clients) if client.spectator]

    def remove_client(self: "GameServer", client: ClientData) -> None:
        self.clients.remove(client)
        if not client.spectator:
            for player in self.game.players:
                if player.name == client.name:
                    player.blocked = True

    def _wait_connections(self: "GameServer") -> None:
        while not self.players:
            print("Waiting for player clients")
            sleep(1)

        for second in range(1, server_connection_timeout + 1):
            names = [player.name for player in self.players]
            print(
                f"Waiting other players ({second}/{server_connection_timeout}) {names}",
            )
            if len(self.players) == MAX_NB_PLAYERS:
                break
            sleep(1)

        print("Players ready: START!!!")
        self.game.start()
        for player in self.players:
            self.write(player, "START")

    def read(self, client: ClientData) -> str:
        try:
            text = client.network.readline()
        except NetworkError:
            logging.exception("timeout for client %s", client.name)
            self.remove_client(client)
            return ""

        logging.debug(text)
        return text

    def write(self, client: ClientData, text: str) -> None:
        if not text.endswith("\n"):
            text += "\n"
        logging.debug("sending to %s", client.name)
        try:
            client.network.write(text)
        except (NetworkError, TimeoutError):
            logging.exception("Problem sending state to client")
            self.remove_client(client)

    def run(self: "GameServer") -> None:
        while True:
            start = perf_counter()
            # refresh spectators every 33 ms
            while perf_counter() - start < 0.033:
                for player_id, player in enumerate(self.players):
                    if player.network.input_empty():
                        continue
                    command = self.read(player)
                    logging.info("Command [%s] %s", player.name, command)
                    self.write(player, self.game.manage_command(player_id, command))
            self.game.update()
            for spectator in self.spectators:
                self.write(spectator, json.dumps(self.game.state()))

            if self.game.cumulated_time > MAX_GAME_DURATION:
                logging.info("Reached time limit for the game")
                break
            if self.game.all_planets_collected:
                logging.info("A player collected all planets, end of the game")
                break
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game server.")
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        help="name of server on the network",
        default="localhost",
    )
    parser.add_argument(
        "-p", "--port", type=int, help="location where server listens", default=16210,
    )
    parser.add_argument("-f", "--fast", help="fast simulation", action="store_true")
    parser.add_argument(
        "-t",
        "--timeout",
        help="timeout in seconds while waiting 2nd, 3rd and 4th players",
        type=int,
        default=10,
    )

    args = parser.parse_args()
    server_connection_timeout = args.timeout

    if args.fast:
        logging.basicConfig(handlers=[logging.NullHandler()])
        with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
            GameServer(args.address, args.port, args.fast).run()
    else:
        logging.basicConfig(
            filename="server.log",
            encoding="utf-8",
            level=logging.INFO,
            format=(
                "%(asctime)s [%(levelname)-8s] %(filename)20s(%(lineno)3s):"
                "%(funcName)-20s :: %(message)s"
            ),
            datefmt="%m/%d/%Y %H:%M:%S",
        )
        logging.info("Launching server")
        GameServer(args.address, args.port).run()
