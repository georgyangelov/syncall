import syncall

from events import Event


class RemoteStore:
    """ Manages communication to a single remote SyncAll instance. """

    def __init__(self, messanger):
        self.messanger = messanger
        self.file_transport = syncall.FileTransport(self)

        self.address = self.messanger.address[0]

        self.disconnected = Event()
        self.messanger.disconnected += self.__disconnected

    def __disconnected(self, no_data):
        self.disconnected.notify(self)

    def disconnect(self):
        self.messanger.disconnect()

    def sync_dir(self):
        """ Syncronizes local and remote directory. """
        pass

    def sync_file(self):
        """ Syncronizes a single file to the remote """
        pass
