class RemoteStoreManager:
    """ Manages multiple remotes """

    def __init__(self, network_discovery):
        self.remotes = dict()

        self.network_discovery = network_discovery

        self.network_discovery.client_discovered += self.__client_discovered
        self.network_discovery.request()

    def __client_discovered(self, remote_ip):
        if remote_ip in self.remotes:
            # TODO: Construct messanger, file_transport and RemoteStore,
            # then add to self.remotes
