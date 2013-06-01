import syncall
import logging

from events import Event


class RemoteStore:
    """ Manages communication to a single remote SyncAll instance. """

    def __init__(self, messanger):
        self.logger = logging.getLogger(__name__)

        self.messanger = messanger
        self.file_transport = syncall.FileTransport(self)

        self.address = self.messanger.address[0]

        self.disconnected = Event()
        self.messanger.disconnected += self.__disconnected
        self.messanger.packet_received += self._packet_received

        self.messanger.start_receiving()
        self.messanger.send({'msg': 'Hello world!'})

    def __disconnected(self, no_data):
        self.disconnected.notify(self)

    def disconnect(self):
        self.messanger.disconnect()

    def _packet_received(self, packet):
        self.logger.debug("Received packet from {}: {}".format(
            self.address,
            packet
        ))

    def sync_dir(self):
        """ Syncronizes local and remote directory. """
        pass

    def sync_file(self):
        """ Syncronizes a single file to the remote """
        pass
