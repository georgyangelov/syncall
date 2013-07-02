import syncall
import logging

from events import Event


MSG_INDEX = 1
MSG_REQUEST_INDEX = 2
MSG_INDEX_DELTA = 3
MSG_INDEX_NO_CHANGE = 4


class RemoteStore:
    """ Manages communication to a single remote SyncAll instance. """

    def __init__(self, messanger, directory):
        self.logger = logging.getLogger(__name__)

        self.messanger = messanger
        self.directory = directory

        self.my_index_last_updated = 0
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
        self.send_index(request=False)

    def send_index(self, request=True):
        if self.my_index_last_updated == self.directory.get_last_update():
            # Nothing to do here, index is already up-to-date
            self.logger.debug(
                "Index update requested but there are no changes"
            )

            self.messanger.send({
                'type': MSG_INDEX_NO_CHANGE
            })

            return

        self.my_index_last_updated = self.directory.get_last_update()

        self.messanger.send({
            'type': MSG_INDEX,
            'index': self.directory.get_index()
        })

        if request:
            self.messanger.send({
                'type': MSG_REQUEST_INDEX
            })

    def send_index_delta(self, changes, request=True):
        """
        Send only the changed files (`changes`) index data to the remote.
        Use ONLY when ALL changed files are sent this way.
        """
        self.my_index_last_updated = self.directory.get_last_update()

        index = self.directory.get_index()
        self.messanger.send({
            'type': MSG_INDEX_DELTA,
            'index': {file_name: index[file_name] for file_name in changes}
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
        if 'type' not in packet:
            self.logger.error("Received packet with no type from {}".format(
                self.address
            ))
            return

        self.logger.debug("Received packet from {}: {}".format(
            self.address,
            packet['type']
        ))

        if packet['type'] == MSG_INDEX:
            self.remote_index = packet['index']
            self.__remote_index_updated()

        elif packet['type'] == MSG_INDEX_DELTA:
            for file_name, file_data in packet['index'].items():
                self.remote_index[file_name] = file_data

            self.__remote_index_updated()

        elif packet['type'] == MSG_REQUEST_INDEX:
            self.send_index(request=False)

        elif packet['type'] == MSG_INDEX_NO_CHANGE:
            self.__remote_index_updated()

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
