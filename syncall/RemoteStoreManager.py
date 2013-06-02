import logging

import syncall


class RemoteStoreManager:
    """ Manages multiple remotes """

    def __init__(self, network_discovery, connection_listener, directory, id):
        self.logger = logging.getLogger(__name__)
        self.remotes = dict()

        self.directory = directory
        self.uuid = id

        self.connection_listener = connection_listener
        connection_listener.connection_establiashed += self.__client_connected

        self.network_discovery = network_discovery
        self.network_discovery.client_discovered += self.__client_discovered
        self.network_discovery.request()

    def __client_connected(self, messanger):
        remote_ip = messanger.address[0]
        remote_uuid = messanger.remote_uuid

        if remote_uuid in self.remotes:
            self.remotes[remote_uuid].disconnect()

        remote_store = syncall.RemoteStore(messanger, self.directory)
        remote_store.disconnected += self.__client_disconnected

        self.remotes[remote_uuid] = remote_store
        self.logger.info(
            "Remote connected from {}, UUID={}"
            .format(remote_ip, messanger.remote_uuid)
        )

        remote_store.start_receiving()

    def __client_discovered(self, data):
        remote_ip = data['source']
        remote_uuid = data['data']['uuid']

        if remote_uuid not in self.remotes:
            messanger = syncall.Messanger.connect(
                (remote_ip, syncall.DEFAULT_PORT),
                self.uuid,
                remote_uuid
            )

            remote_store = syncall.RemoteStore(messanger, self.directory)

            self.remotes[remote_uuid] = remote_store
            self.logger.info(
                "Connected to a remote at {}, UUID={}"
                .format(remote_ip, remote_uuid)
            )

            remote_store.start_receiving()

    def __client_disconnected(self, remote):
        self.logger.info(
            "Remote at {} disconnected, UUID={}"
            .format(remote.address, remote.uuid)
        )

        del self.remotes[remote.uuid]
