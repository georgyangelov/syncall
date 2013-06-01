import socket
import msgpack
import logging

from socketserver import UDPServer, DatagramRequestHandler
from threading import Thread

from events import Event
from bintools import decode_object


BROADCAST_ADDRESS = '255.255.255.255'


class NetworkDiscovery:
    """ Discovers remote SyncAll instances on the same network. """

    def __init__(self, port, version, uuid):
        self.logger = logging.getLogger(__name__)

        # Store UUID based on the hostname and current time to check
        # if the received broadcast packet is from self
        self.uuid = uuid

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
        self.__broadcast({
            'version': self.version,
            'uuid': self.uuid
        }, self.port)

    def __broadcast(self, data, port):
        self.socket.sendto(msgpack.packb(data), (BROADCAST_ADDRESS, port))

    def __receive_packet(self, data):
        if self.__is_self(data):
            return

        self.logger.debug("Received discovery request from {}"
                          .format(data['source']))

        del data['server']

        self.client_discovered.notify(data)

    def __is_self(self, data):
        return data['data']['uuid'] == self.uuid


class BroadcastEventNotifierHandler(DatagramRequestHandler):
    def setup(self):
        self.logger = logging.getLogger(__name__)

        super().setup()

    def handle(self):
        try:
            self.logger.debug("Received UDP packet from {}"
                              .format(self.client_address[0]))

            data = decode_object(msgpack.unpackb(self.packet))
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
        UDPServer.__init__(self, ('', port), BroadcastEventNotifierHandler)
        Thread.__init__(self)
        self.daemon = True

        self.packet_received = Event()
        self.packet_received_error = Event()

        self.allow_reuse_address = 1

    def run(self):
        self.serve_forever()
