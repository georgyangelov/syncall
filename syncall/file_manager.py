import logging

from threading import Thread


class FileManager:
    def __init__(self, remote):
        self.logger = logging.getLogger(__name__)

        self.remote = remote
        self.directory = remote.directory

        self.transfers_lock = threading.Lock()

        self.transfers = dict()

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


class FileTransfer(Thread):
    def __init__(self, file_data):
        super().__init__()

        self.file_data = file_data

    def shutdown(self):
        pass

    def run(self):
        # Transfer a file to the remote end
        pass


class FileTransferListener(Thread):
    def __init__(self, remote):
        super().__init__()

        self.remote = remote

    def run(self):
        pass
