import logging
import threading

from events import Event
import syncall


class TransferManager:
    def __init__(self, remote):
        self.logger = logging.getLogger(__name__)

        self.remote = remote
        self.directory = remote.directory

        self.transfers_lock = threading.Lock()

        self.transfers = dict()

    def process_transfer(self, messanger):
        """
        Verify the request is legit, wrap it in a FileTransfer object
        and make sure it's tracked
        """
        with self.transfers_lock:
            if self.remote.address != messanger.address[0]:
                # Someone's trying to impersonate a remote?!?
                self.logger.debug(
                    "Transfer initiated from a non-expected address: {}"
                    .format(messanger.address[0])
                )
                messanger.disconnect()
                return

            # TODO

    def sync_file(self, file, lock=True):
        with self.transfers_lock:
            if file in self.transfers:
                transfer = self.transfers[file]

                if transfer.file_data != self.directory.get_index()[file]:
                    transfer.shutdown()
                    del self.transfers[file]

            self.logger.debug("Syncing {}".format(file))

            # File is guaranteed to be indexed locally
            # so the `file` key exists
            transfer = FileTransfer(self.directory.get_index()[file])
            self.transfers[file] = transfer

            transfer.start()

    def sync_files(self, file_list):
        for file in file_list:
            self.sync_file(file)

    def stop_transfers(self):
        with self.transfers_lock:
            for file, transfer in self.transfers.items():
                transfer.shutdown()

            self.transfers.clear()


class FileTransfer(threading.Thread):
    # Message types
    MSG_INIT = 0
    MSG_ACCEPT = 1
    MSG_CANCEL = 2

    def __init__(self, directory, messanger, file_name=None):
        super().__init__()

        self.directory = directory
        self.messanger = messanger

        self.file_name = file_name
        self.remote_file_data = None

        self.messanger.packet_received += self.__packet_received
        self.messanger.disconnected += self.__disconnected

        self.__transfer_started = False
        self.__transfer_complete = False
        self.__transfer_cancelled = False

        self.transfer_complete = Event()
        self.transfer_failed = Event()
        self.transfer_cancelled = Event()

        self.messanger.start_receiving()

    def is_done(self):
        return self.__transfer_cancelled or self.__transfer_complete

    def has_started(self):
        return self.__transfer_started

    def shutdown(self):
        self.__transfer_cancelled = True
        self.transfer_cancelled.notify()

        self.messanger.send({
            "type": self.MSG_CANCEL
        })
        self.messanger.shutdown()

    def terminate(self):
        self.messanger.shutdown()

    def start(self):
        """
        Transfer a file to the remote end. Do not call this if
        a transfer request should be handled.
        """
        if self.file_name is None:
            raise ValueError("file_name is None. Cannot transfer unknown file")

        self.__transfer_started = True

        self.messanger.send({
            "type": self.MSG_INIT_TRANSFER,
            "name": self.file_name,
            "data": self.directory.get_index()[self.file_name]
        })

    def __transfer_file(self):
        self.logger.debug(
            "Started transferring file {} to remote {}"
            .format(self.file_name, self.messanger.address[0])
        )
        super().start()

    def run(self):
        """
        Send the delta data to the remote side.
        """
        pass

    def __accept_file(self, file_name, file_data):
        """
        Make sure the file needs to be transfered
        and accept it if it does.
        """
        file_status = syncall.IndexDiff.compare_file(
            file_data,
            self.directory.get_index()[file_name]
        )

        if file_status == NEEDS_UPDATE:
            self.file_name = file_name
            self.remote_file_data = file_data
            self.__transfer_started = True

            self.messanger.send({
                "type": self.MSG_ACCEPT,
                "checksums": self.directory.get_block_checksums(self.file_name)
            })
            self.logger.debug(
                "Accepted a file transfer request for {} from {}"
                .format(file_name, self.messanger.address[0])
            )
        else:
            self.logger.error(
                "File transfer requested for {} from {} shouldn't be updated"
                .format(file_name, self.messanger.address[0])
            )
            self.shutdown()

    def __packet_received(self, data):
        if data['type'] == self.MSG_INIT_TRANSFER:
            self.__accept_file(self, data['name'], data['data'])

        elif data['type'] == self.MSG_ACCEPT:
            self.__transfer_file()

        elif data['type'] == self.MSG_CANCEL:
            self.__transfer_cancelled = True
            self.transfer_cancelled.notify()

        else:
            self.logger.error("Unknown packet from {}: {}".format(
                self.messanger.address[0],
                packet['type']
            ))

    def __disconnected(self, data):
        if not self.__transfer_cancelled and not self.__transfer_complete:
            self.transfer_failed.notify()
