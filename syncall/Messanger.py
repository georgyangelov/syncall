import msgpack
import logging
import socket

import bintools

from socketserver import TCPServer, StreamRequestHandler
from threading import Thread

from events import Event


class Messanger(Thread):
    """ Delivers and receives packets to/from remote instances using TCP. """

    BUFFER_SIZE = 1024

    def __init__(self, socket, address):
        super().__init__()
        self.daemon = True

        self.logger = logging.getLogger(__name__)

        self.packet_received = Event()
        self.disconnected = Event()

        self.address = address
        self.socket = socket

        self.__unpacker = msgpack.Unpacker()

    @staticmethod
    def connect(address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        return Messanger(sock, address)

    def disconnect(self):
        try:
            self.socket.close()
        except:
            pass

    def start_receiving(self):
        self.start()

    def run(self):
        with self.socket:
            while True:
                try:
                    data = self.socket.recv(self.BUFFER_SIZE)
                except ConnectionResetError:
                    break

                if not data:
                    break

                self.__handle_received_data(data)

        self.logger.debug("Connection to {} closed".format(self.address[0]))
        self.disconnected.notify()
        self.disconnected.clear_handlers()
        self.packet_received.clear_handlers()

    def send(self, data):
        packet = msgpack.packb(data)

        self.socket.send(packet)

    def __handle_received_data(self, data):
        self.__unpacker.feed(data)

        for packet in self.__unpacker:
            unpacked_packet = bintools.decode_object(packet)
            try:
                self.packet_received.notify(unpacked_packet)
            except Exception as ex:
                self.logger.error("Error processing packet from {}"
                                  .format(self.address[0]))
                self.logger.exception(ex)


class ConnectionListener(Thread):
    def __init__(self, port):
        super().__init__()
        self.daemon = True

        self.address = ('', port)
        self.connection_establiashed = Event()

    def run(self):
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.bind(self.address)
        serversock.listen(5)

        while True:
            client_socket, client_address = serversock.accept()

            self.connection_establiashed(
                Messanger(client_socket, client_address)
            )
