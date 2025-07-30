import logging
from threading import Thread
from time import sleep

from space_collector.network.data_handler import NetworkError
from space_collector.network.client import Client
from space_collector.viewer.window import input_queue, gui_thread


def network_thread(server_addr: str, port: int) -> None:
    client = Client(server_addr, port, spectator=True)
    while True:
        try:
            data = client.read_json(timeout=3600)
            input_queue.put(data)
        except NetworkError:
            logging.exception("End of network communication")
            break
    for _ in range(6):
        sleep(10)
        logging.info("sleeping")


class Viewer:
    def __init__(self, server_addr: str, port: int) -> None:
        logging.info("Start network")
        Thread(target=network_thread, daemon=True, args=[server_addr, port]).start()
        logging.info("Start GUI")
        gui_thread(server_addr, port)
