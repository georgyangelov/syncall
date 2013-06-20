import logging
import threading
import os
import pyrsync2

from io import BytesIO

from events import Event
import syncall


class TransferManager:
    def __init__(self, remote):
        self.logger = logging.getLogger(__name__)

        self.remote = remote
        self.directory = remote.directory

        self.transfers_lock = threading.Lock()

        self.transfers = dict()

    def process_transfer(self, messanger):
        """
        Verify the request is legit, wrap it in a FileTransfer object
        and make sure it's tracked
        """
        with self.transfers_lock:
            if self.remote.address != messanger.address[0]:
                # Someone's trying to impersonate a remote?!?
                self.logger.debug(
                    "Transfer initiated from a non-expected address: {}"
                    .format(messanger.address[0])
                )
                messanger.disconnect()
                return

            transfer = FileTransfer(
                self.directory,
                messanger
            )

            self.hook_events(transfer, start_event=True)

    def sync_file(self, file, lock=True):
        with self.transfers_lock:
            if file in self.transfers:
                transfer = self.transfers[file]

                if transfer.file_data != self.directory.get_index()[file]:
                    transfer.shutdown()
                    del self.transfers[file]

            self.logger.debug("Syncing {}".format(file))

            messanger = syncall.Messanger.connect(
                (self.remote.address, syncall.DEFAULT_TRANSFER_PORT),
                self.remote.my_uuid,
                self.remote.uuid
            )

            # File is guaranteed to be indexed locally
            # so the `file` key exists
            transfer = FileTransfer(
                self.directory,
                messanger,
                file,
                syncall.DEFAULT_BLOCK_SIZE
            )
            self.transfers[file] = transfer

            self.hook_events(transfer, start_event=False)
            transfer.start()

    def hook_events(self, transfer, start_event=True):
        transfer.transfer_completed += self.__transfer_completed
        transfer.transfer_failed += self.__transfer_failed
        transfer.transfer_cancelled += self.__transfer_cancelled

        if start_event:
            transfer.transfer_started += self.__transfer_started

        transfer.initialize()

    def __transfer_started(self, transfer):
        if transfer.file_name in self.transfers:
            self.logger.debug(
                "Transfer initiated but another transfer for this file"
                " is already running"
            )
            return

        self.transfers[transfer.file_name] = transfer

    def __transfer_completed(self, transfer):
        # TODO: Update the file

        self.logger.debug(
            "Transfer of {} : {} completed"
            .format(transfer.file_name, self.remote.address)
        )

        with self.transfers_lock:
            if transfer.file_name in self.transfers:
                del self.transfers[transfer.file_name]

    def __transfer_failed(self, transfer):
        self.logger.debug(
            "Transfer of {} : {} failed"
            .format(transfer.file_name, self.remote.address)
        )

        if transfer.file_name in self.transfers:
            del self.transfers[transfer.file_name]

    def __transfer_cancelled(self, transfer):
        self.logger.debug(
            "Transfer of {} : {} was cancelled"
            .format(transfer.file_name, self.remote.address)
        )

        if transfer.file_name in self.transfers:
            del self.transfers[transfer.file_name]

    def sync_files(self, file_list):
        for file in file_list:
            self.sync_file(file)

    def stop_transfers(self):
        with self.transfers_lock:
            for transfer in list(self.transfers.values()):
                transfer.shutdown()

        self.transfers.clear()


class FileTransfer(threading.Thread):
    # Message types
    MSG_INIT = 0
    MSG_INIT_ACCEPT = 1
    MSG_CANCEL = 2
    MSG_BLOCK_DATA = 3
    MSG_DONE = 4
    MSG_DONE_ACCEPT = 5

    def __init__(self, directory, messanger, file_name=None, block_size=4098):
        super().__init__()

        self.logger = logging.getLogger(__name__)

        self.directory = directory
        self.messanger = messanger

        self.file_name = file_name
        self.block_size = block_size
        self.remote_file_data = None
        self.remote_checksums = None

        self.messanger.packet_received += self.__packet_received
        self.messanger.disconnected += self.__disconnected

        self.__transfer_started = False
        self.__transfer_completed = False
        self.__transfer_cancelled = False

        self.__temp_file_name = None
        self.__temp_file_handle = None
        self.__file_handle = None

        self.transfer_started = Event()
        self.transfer_completed = Event()
        self.transfer_failed = Event()
        self.transfer_cancelled = Event()

    def initialize(self):
        self.messanger.start_receiving()

    def is_done(self):
        return self.__transfer_cancelled or self.__transfer_completed

    def has_started(self):
        return self.__transfer_started

    def shutdown(self):
        self.__transfer_cancelled = True
        self.transfer_cancelled.notify(self)

        self.messanger.send({
            "type": self.MSG_CANCEL
        })
        self.messanger.disconnect()
        self.__release_resources()

    def terminate(self):
        self.messanger.disconnect()
        self.__release_resources()

    def __release_resources(self):
        if self.__temp_file_handle is not None:
            self.__temp_file_handle.close()
            self.__temp_file_handle = None

        if self.__file_handle is not None:
            self.__file_handle.close()
            self.__file_handle = None

        if self.__temp_file_name is not None:
            self.directory.release_temp_file(self.__temp_file_name)
            self.__temp_file_name = None

    def start(self):
        """
        Transfer a file to the remote end. Do not call this if
        a transfer request should be handled.
        """
        if self.file_name is None:
            raise ValueError("file_name is None. Cannot transfer unknown file")

        self.__transfer_started = True
        self.transfer_started.notify(self)

        self.messanger.send({
            "type": self.MSG_INIT,
            "name": self.file_name,
            "data": self.directory.get_index()[self.file_name]
        })

    def __transfer_file(self, remote_checksums, block_size):
        self.logger.debug(
            "Started transferring file {} to remote {}"
            .format(self.file_name, self.messanger.address[0])
        )

        self.block_size = block_size
        self.remote_checksums = remote_checksums

        super().start()

    def run(self):
        """
        Send the delta data to the remote side.
        """
        try:
            with open(self.directory.get_file_path(self.file_name), 'rb') \
                    as file:
                delta_generator = pyrsync2.rsyncdelta(
                    file,
                    self.remote_checksums,
                    blocksize=self.block_size,
                    max_buffer=self.block_size
                )

                # Actual transfer of data
                for block in delta_generator:
                    self.messanger.send({
                        "type": self.MSG_BLOCK_DATA,
                        "binary_data": block
                    })
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.error(
                "File {} couldn't be read transferred to {}. Maybe it changed."
                .format(self.file_name, self.messanger.address[0])
            )
            self.shutdown()
        else:
            self.messanger.send({
                "type": self.MSG_DONE
            })

    def __accept_file(self, file_name, file_data):
        """
        Make sure the file needs to be transferred
        and accept it if it does.
        """
        file_status = syncall.IndexDiff.compare_file(
            file_data,
            self.directory.get_index().get(file_name, None)
        )

        if file_status == syncall.index.NEEDS_UPDATE:
            self.file_name = file_name
            self.remote_file_data = file_data
            self.__temp_file_name = self.directory.get_temp_path(
                self.file_name
            )
            self.__temp_file_handle = open(self.__temp_file_name, 'wb')

            if os.path.exists(self.directory.get_file_path(self.file_name)):
                self.__file_handle = open(
                    self.directory.get_file_path(self.file_name),
                    'rb'
                )
            else:
                self.__file_handle = BytesIO()

            self.__transfer_started = True
            self.transfer_started.notify(self)

            self.messanger.send({
                "type": self.MSG_INIT_ACCEPT,
                "block_size": self.block_size,
                "checksums": self.directory.get_block_checksums(
                    self.file_name,
                    self.block_size
                )
            })
            self.logger.debug(
                "Accepted a file transfer request for {} from {}"
                .format(file_name, self.messanger.address[0])
            )
        else:
            self.logger.error(
                "File transfer requested for {} from {} shouldn't be updated"
                .format(file_name, self.messanger.address[0])
            )
            self.shutdown()

    def __packet_received(self, data):
        if data['type'] == self.MSG_INIT:
            self.__accept_file(data['name'], data['data'])

        elif data['type'] == self.MSG_INIT_ACCEPT:
            self.__transfer_file(data['checksums'], data['block_size'])

        elif data['type'] == self.MSG_CANCEL:
            self.__transfer_cancelled = True
            self.terminate()
            self.transfer_cancelled.notify(self)

        elif data['type'] == self.MSG_BLOCK_DATA:
            if not self.__transfer_started:
                self.logger.error(
                    "Received data from {} for {}, but transfer not started"
                    .format(self.messanger.address[0], self.file_name)
                )
                self.terminate()

            self.__data_received(data['binary_data'])

        elif data['type'] == self.MSG_DONE:
            self.__complete_transfer()

        elif data['type'] == self.MSG_DONE_ACCEPT:
            self.__transfer_completed = True
            self.terminate()

            self.transfer_completed.notify(self)

        else:
            self.logger.error("Unknown packet from {}: {}".format(
                self.messanger.address[0],
                packet['type']
            ))

    def __data_received(self, block):
        try:
            pyrsync2.patchstream_block(
                self.__file_handle,
                self.__temp_file_handle,
                block,
                blocksize=self.block_size
            )
        except Exception as ex:
            self.logger.exception(ex)
            self.logger.error(
                "Block couldn't be applied to temp file of {}. Remote: {}"
                .format(self.file_name, self.messanger.address[0])
            )
            self.shutdown()

    def __complete_transfer(self):
        self.messanger.send({
            'type': self.MSG_DONE_ACCEPT
        })

        # Remote side should disconnect after MSG_DONE_ACCEPT
        self.__transfer_completed = True

        self.transfer_completed.notify(self)

    def __disconnected(self, data):
        self.__release_resources()

        if not self.__transfer_cancelled and not self.__transfer_completed:
            self.transfer_failed.notify(self)
