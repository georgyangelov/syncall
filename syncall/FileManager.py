from threading import Thread


class FileManager:
    def __init__(self, remote):
        self.remote = remote
        self.directory = remote.directory

    def send_file(self, file):
        pass


class FileTransfer(Thread):
    def __init__(self):
        super().__init__()
