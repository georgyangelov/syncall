import socket
import msgpack
import logging

from socketserver import UDPServer, DatagramRequestHandler
from threading import Thread

from events import Event


BROADCAST_ADDRESS = '255.255.255.255'


class NetworkDiscovery:
    """ Discovers remote SyncAll instances on the same network. """

    def __init__(self, port, version):
        self.logger = logging.getLogger(__name__)

        self.client_discovered = Event()

        self.port = port
        self.version = version
        self.listener = BroadcastListener(self.port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.listener.packet_received += self.__receive_packet

    def start_listening(self):
        self.listener.start()

    def request(self):
        """ Sends a discovery request to all hosts on the LAN """
        self.__broadcast({'version': self.version}, self.port)

    def __broadcast(self, data, port):
        self.socket.sendto(msgpack.packb(data), (BROADCAST_ADDRESS, port))

    def __receive_packet(self, data):
        self.logger.debug("Received discovery response from {}"
                          .format(data['source']))

        self.client_discovered.notify(data['source'])


class BroadcastEventNotifierHandler(DatagramRequestHandler):
    def setup(self):
        self.logger = logging.getLogger(__name__)

        super().setup()

    def handle(self):
        try:
            self.logger.debug("Received UDP packet from {}"
                              .format(self.client_address[0]))

            data = msgpack.unpackb(self.packet)
            self.server.packet_received.notify({
                'data': data,
                'source': self.client_address[0],
                'server': self.server
            })
        except msgpack.exceptions.UnpackException as ex:
            self.logger.exception("Error unpacking UDP data", ex)
            self.server.packet_received_error.notify(self.packet)
        except Exception as ex:
            self.logger.exception("Error processing UDP data", ex)


class BroadcastListener(UDPServer, Thread):
    def __init__(self, port):
        self.packet_received = Event()
        self.packet_received_error = Event()

        self.allow_reuse_address = 1
        UDPServer.__init__(self, ('', port), BroadcastEventNotifierHandler)
        Thread.__init__(self)

    def run(self):
        self.serve_forever()
