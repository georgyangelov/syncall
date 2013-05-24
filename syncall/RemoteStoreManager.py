from syncall import Messanger, RemoteStore


class RemoteStoreManager:
    """ Manages multiple remotes """

    def __init__(self, network_discovery):
        self.remotes = dict()

        self.network_discovery = network_discovery

        self.network_discovery.client_discovered += self.__client_discovered
        self.network_discovery.request()

    def __client_discovered(self, remote_ip):
        if remote_ip not in self.remotes:
            messanger = Messanger.connect((remote_ip, syncall.DEFAULT_PORT))
            # TODO: Create FileTransport
            file_transport = None

            remote_store = RemoteStore(messanger, file_transport)

            self.remotes.add(remote_store)
