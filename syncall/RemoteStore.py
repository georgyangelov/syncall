import syncall


class RemoteStore:
    """ Manages communication to a single remote SyncAll instance. """

    def __init__(self, messanger):
        self.messanger = messanger
        self.file_transport = syncall.FileTransport(self)

    def sync_dir(self):
        """ Syncronizes local and remote directory. """
        pass

    def sync_file(self):
        """ Syncronizes a single file to the remote """
        pass
