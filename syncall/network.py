import msgpack
import logging
import socket
import uuid

import bintools

from socketserver import TCPServer, StreamRequestHandler
from threading import Thread

from events import Event


class Messanger(Thread):
    """ Delivers and receives packets to/from remote instances using TCP. """

    BUFFER_SIZE = 1024 * 1024
    CONNECT_TIMEOUT = 5

    def __init__(self, socket, address, my_uuid, remote_uuid):
        super().__init__()
        # self.daemon = True

        self.logger = logging.getLogger(__name__)

        self.packet_received = Event()
        self.disconnected = Event()

        self.address = address
        self.socket = socket

        self.my_uuid = my_uuid
        self.remote_uuid = remote_uuid

        self.__unpacker = msgpack.Unpacker()

    @staticmethod
    def connect(address, my_uuid, remote_uuid):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.settimeout(Messanger.CONNECT_TIMEOUT)
        sock.connect(address)
        sock.sendall(uuid.UUID(my_uuid).bytes)
        sock.settimeout(None)

        return Messanger(sock, address, my_uuid, remote_uuid)

    def disconnect(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass

    def start_receiving(self):
        self.start()

    def run(self):
        with self.socket:
            while True:
                try:
                    data = self.socket.recv(self.BUFFER_SIZE)
                except:
                    break

                if not data:
                    break

                self.__handle_received_data(data)

        self.disconnected.notify()
        self.disconnected.clear_handlers()
        self.packet_received.clear_handlers()

    def send(self, data):
        packet = msgpack.packb(data)

        try:
            self.socket.send(packet)
        except Exception as ex:
            self.logger.error(
                "Couldn't send data to {}"
                .format(self.address[0])
            )
            self.disconnect()

    def __handle_received_data(self, data):
        self.__unpacker.feed(data)

        for packet in self.__unpacker:
            try:
                unpacked_packet = bintools.decode_object(
                    packet,
                    except_keys=('hash', 'binary_data')
                )
            except Exception as ex:
                self.logger.error(
                    "Error trying to decode strings to utf-8 in packet from {}"
                    .format(self.address[0])
                )
                self.logger.exception(ex)
            else:
                try:
                    self.packet_received.notify(unpacked_packet)
                except Exception as ex:
                    self.logger.error("Error processing packet from {}"
                                      .format(self.address[0]))
                    self.logger.exception(ex)


class ConnectionListener(Thread):
    UUID_BYTE_LENGTH = 16

    def __init__(self, my_uuid, port):
        super().__init__()
        # self.daemon = True

        self.logger = logging.getLogger(__name__)

        self.my_uuid = my_uuid
        self.address = ('', port)
        self.connection_establiashed = Event()

    def shutdown(self):
        self.serversock.close()

    def run(self):
        self.serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversock.bind(self.address)
        self.serversock.listen(5)
        self.serversock.settimeout(1)

        while True:
            try:
                client_socket, client_address = self.serversock.accept()
            except socket.timeout:
                continue
            except:
                break

            try:
                # UUID_BYTE_LENGTH bytes with the UUID should be the first
                # thing on the stream

                uuid_bytes = b''
                error = False

                while len(uuid_bytes) < self.UUID_BYTE_LENGTH:
                    new_uuid_bytes = client_socket.recv(
                        self.UUID_BYTE_LENGTH - len(uuid_bytes)
                    )

                    if len(new_uuid_bytes) == 0:
                        error = True

                    uuid_bytes += new_uuid_bytes

                if error:
                    self.logger.error(
                        "Remote tried to connect, but the UUID couldn't be "
                        "transfered properly. Closing connection..."
                    )
                    try:
                        client_socket.close()
                    except:
                        pass
                    continue

                remote_uuid = str(uuid.UUID(bytes=uuid_bytes))

                self.connection_establiashed(
                    Messanger(
                        client_socket,
                        client_address,
                        self.my_uuid,
                        remote_uuid
                    )
                )
            except Exception as ex:
                self.logger.error(
                    "Exception while accepting connection from {}"
                    .format(client_address[0])
                )
                self.logger.exception(ex)
