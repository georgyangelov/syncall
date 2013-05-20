import msgpack

from socketserver import TCPServer, StreamRequestHandler
from threading import Thread

from events import Event


class Messanger:
    """ Delivers and receives TCP packets to/from remote instances. """

    def __init__(self, remote_ip, remote_port):
        self.packet_received = self.listener.packet_received

        self.address = (remote_ip, remote_port)
        # self.socket =
        # TODO: TCPConnectionListener otdelen klas, tuk rabota s vrazkata samo
        self.listener = PacketListener(self.address)

    def start_listening(self):
        self.listener.start()

    def connect(self, data):
        packet = msgpack.packb(data)


class PacketListener(TCPServer, Thread):
    def __init__(self, address):
        self.packet_received = Event()
        self._unpacker = msgpack.Unpacker()

        super().__init__(address, EventNotifierPacketHandler)

    def run(self):
        self.serve_forever()


class EventNotifierPacketHandler(StreamRequestHandler):
    def handle(self):
        unpacker = self.server._unpacker

        unpacker.feed(self.rfile)

        for packet in unpacker:
            self.server.packet_received.notify(packet)
