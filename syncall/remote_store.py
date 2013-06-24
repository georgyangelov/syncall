import syncall
import logging

from events import Event


MSG_INDEX = 1
MSG_REQUEST_INDEX = 2


class RemoteStore:
    """ Manages communication to a single remote SyncAll instance. """

    def __init__(self, messanger, directory):
        self.logger = logging.getLogger(__name__)

        self.messanger = messanger
        self.directory = directory

        self.remote_index = None

        self.address = self.messanger.address[0]
        self.my_uuid = self.messanger.my_uuid
        self.uuid = self.messanger.remote_uuid

        self.disconnected = Event()
        self.messanger.disconnected += self.__disconnected
        self.messanger.packet_received += self._packet_received

    def request_transfer(self, transfer_messanger):
        # Pass the transfer request to the transfer manager
        self.directory.transfer_manager.process_transfer(
            self,
            transfer_messanger
        )

    def index_received(self):
        return self.remote_index is not None

    def start_receiving(self):
        self.messanger.start_receiving()
        self.send_index()

    def send_index(self, request=True):
        self.messanger.send({
            'type': MSG_INDEX,
            'index': self.directory.get_index()
        })

        if request:
            self.messanger.send({
                'type': MSG_REQUEST_INDEX
            })

    def __disconnected(self, no_data):
        self.directory.transfer_manager.remote_disconnect(self)
        self.disconnected.notify(self)

    def disconnect(self):
        self.messanger.disconnect()

    def _packet_received(self, packet):
        self.logger.debug("Received packet from {}: {}".format(
            self.address,
            packet['type']
        ))

        if 'type' not in packet:
            self.logger.error("Received packet with no type from {}".format(
                self.address
            ))

        if packet['type'] == MSG_INDEX:
            self.remote_index = packet['index']
            self.__remote_index_updated()

        elif packet['type'] == MSG_REQUEST_INDEX:
            self.send_index(request=False)

        else:
            self.logger.error("Unknown packet from {}: {}".format(
                self.address,
                packet['type']
            ))

    def __remote_index_updated(self):
        self.logger.debug("{}'s index updated".format(self.address))

        diff = self.directory.diff(self.remote_index)

        if diff[2]:
            self.logger.debug(
                "File conflicts with {}: {}"
                .format(self.uuid, diff[2])
            )

        # TODO: Handle deleted and conflicted files
        self.directory.transfer_manager.sync_files(self, diff[0])
