import msgpack
import logging

from socketserver import TCPServer, StreamRequestHandler
from threading import Thread

from events import Event


class Messanger(Thread):
    """ Delivers and receives TCP packets to/from remote instances. """

    BUFFER_SIZE = 1024

    def __init__(self, socket, address):
        self.logger = logging.getLogger(__name__)

        self.packet_received = Event()
        self.disconnected = Event()

        self.address = address
        self.socket = socket

        self.__unpacker = msgpack.Unpacker()

    def run(self):
        while True:
            data = clientsock.recv(BUFFER_SIZE)

            if not data:
                break

            self.__handle_received_data(data)
            # clientsock.send(msg)

        clientsock.close()
        self.logger.debug("Connection to {} closed"
                          .format(address[0]))

    def send(self, data):
        packet = msgpack.packb(data)

        self.socket.send(packet)

    def __handle_received_data(self, data):
        self.__unpacker.feed(data)

        for packet in self.__unpacker:
            self.packet_received.notify(packet)


class ConnectionListener(Thread):
    def __init__(self, address):
        self.address = address

        self.connection_establiashed = Event()

    def run(self):
        serversock = socket(AF_INET, SOCK_STREAM)
        serversock.bind(self.address)
        serversock.listen(5)

        while True:
            client_socket, client_address = serversock.accept()

            self.connection_establiashed(
                Messanger(client_socket, client_address)
            )
