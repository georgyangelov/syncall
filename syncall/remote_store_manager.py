import logging
import threading

import syncall


class RemoteStoreManager:
    """ Manages multiple remotes """

    def __init__(self, network_discovery, connection_listener,
                 transfer_listener, directory, id):
        self.logger = logging.getLogger(__name__)
        self.remotes = dict()
        self.remotes_lock = threading.Lock()

        self.directory = directory
        self.uuid = id

        self.connection_listener = connection_listener
        connection_listener.connection_establiashed += self.__client_connected

        self.transfer_listener = transfer_listener
        transfer_listener.connection_establiashed += self.__transfer_initiated

        self.network_discovery = network_discovery
        self.network_discovery.client_discovered += self.__client_discovered
        self.network_discovery.request()

        self.directory.index_updated += self.__index_updated

    def shutdown(self):
        # This will trigger their diconnected event and will remove them
        # from the remotes dictionary
        with self.remotes_lock:
            for remote in list(self.remotes.values()):
                remote.disconnect()

    def send_index(self, changed_files=None, force=False):
        with self.remotes_lock:
            if changed_files is None:
                for remote in list(self.remotes.values()):
                    remote.send_index(force=force)
            else:
                for remote in list(self.remotes.values()):
                    remote.send_index_delta(changed_files)

    def __index_updated(self, changed_files):
        if changed_files is None:
            self.send_index(force=True)
        elif changed_files:
            self.logger.debug(
                "Sending index delta to all remotes: {}"
                .format(changed_files)
            )
            self.send_index(changed_files)

    def __transfer_initiated(self, transfer_messanger):
        # Accept the transfer connection and pass it to the
        # appropriate remote store
        remote_uuid = transfer_messanger.remote_uuid

        if remote_uuid not in self.remotes:
            # Transfer request from an unknown remote
            self.logger.debug(
                "Transfer request from an unknown remote at {}, UUID={}"
                .format(transfer_messanger.address[0], remote_uuid)
            )
            transfer_messanger.disconnect()
            return

        self.remotes[remote_uuid].request_transfer(transfer_messanger)

    def __client_connected(self, messanger):
        with self.remotes_lock:
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
        with self.remotes_lock:
            remote_ip = data['source']
            remote_uuid = data['data']['uuid']

            if remote_uuid not in self.remotes:
                try:
                    messanger = syncall.Messanger.connect(
                        (remote_ip, syncall.DEFAULT_PORT),
                        self.uuid,
                        remote_uuid
                    )
                except Exception as ex:
                    self.logger.error(
                        "Couldn't connect to {}".format(remote_ip)
                    )
                    self.logger.exception(ex)

                    return

                remote_store = syncall.RemoteStore(messanger, self.directory)
                remote_store.disconnected += self.__client_disconnected

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
