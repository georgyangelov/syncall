import logging

from threading import Thread


class FileManager:
    def __init__(self, remote):
        self.remote = remote
        self.directory = remote.directory

        self.logger = logging.getLogger(__name__)

    def sync_file(self, file):
        self.logger.debug("Syncing {}".format(file))

    def sync_files(self, file_list):
        for file in file_list:
            self.sync_file(file)

    def stop_transfers(self):
        pass


class FileTransfer(Thread):
    def __init__(self):
        super().__init__()
