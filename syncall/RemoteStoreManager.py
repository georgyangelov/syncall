import logging

import syncall


class RemoteStoreManager:
    """ Manages multiple remotes """

    def __init__(self, network_discovery, connection_listener):
        self.logger = logging.getLogger(__name__)
        self.remotes = dict()

        self.connection_listener = connection_listener
        connection_listener.connection_establiashed += self.__client_connected

        self.network_discovery = network_discovery
        self.network_discovery.client_discovered += self.__client_discovered
        self.network_discovery.request()

    def __client_connected(self, messanger):
        remote_ip = messanger.address[0]

        # TODO: Create FileTransport
        file_transport = None

        remote_store = syncall.RemoteStore(messanger, file_transport)
        self.logger.info("Remote connected from {}".format(remote_ip))

    def __client_discovered(self, remote_ip):
        if remote_ip not in self.remotes:
            messanger = syncall.Messanger.connect(
                (remote_ip, syncall.DEFAULT_PORT)
            )
            # TODO: Create FileTransport
            file_transport = None

            remote_store = syncall.RemoteStore(messanger, file_transport)

            self.remotes[remote_ip] = remote_store
            self.logger.info("Connected to a remote at {}".format(remote_ip))
