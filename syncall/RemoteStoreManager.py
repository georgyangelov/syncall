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

        if remote_ip in self.remotes:
            self.remotes[remote_ip].disconnect()

        remote_store = syncall.RemoteStore(messanger)
        remote_store.disconnected += self.__client_disconnected

        self.remotes[remote_ip] = remote_store
        self.logger.info("Remote connected from {}".format(remote_ip))

    def __client_discovered(self, remote_ip):
        if remote_ip not in self.remotes:
            messanger = syncall.Messanger.connect(
                (remote_ip, syncall.DEFAULT_PORT)
            )

            remote_store = syncall.RemoteStore(messanger)

            self.remotes[remote_ip] = remote_store
            self.logger.info("Connected to a remote at {}".format(remote_ip))

    def __client_disconnected(self, remote):
        self.logger.info("Remote at {} disconnected".format(remote.address))

        del self.remotes[remote.address]
