import logging
import threading


class TransferManager:
    def __init__(self, remote):
        self.logger = logging.getLogger(__name__)

        self.remote = remote
        self.directory = remote.directory

        self.transfers_lock = threading.Lock()

        self.transfers = dict()

    def process_transfer(self, messanger):
        with self.transfers_lock:
            # Verify the request is legit, wrap it in a FileTransfer object
            # and make sure it's tracked
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
    def __init__(self, file_data):
        super().__init__()

        self.file_data = file_data

    def shutdown(self):
        pass

    def run(self):
        # Transfer a file to the remote end
        pass
