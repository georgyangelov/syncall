import logging
import threading
import os
import pathext
import msgpack
import bintools

from bintools import hash_file


class Directory:
    """
    Listens for file system changes in specific directory and applies
    changes from different sources.
    """

    CONFLICT = -1
    NOT_MODIFIED = 0
    NEEDS_UPDATE = 1

    def __init__(self, uuid, dir_path, index_name='.syncall_index',
                 load_index=True):
        self.logger = logging.getLogger(__name__)

        self.uuid = uuid
        self.dir_path = dir_path
        self.index_name = index_name
        self.index_path = os.path.join(self.dir_path, self.index_name)

        self.fs_access_lock = threading.Lock()

        if load_index:
            self.load_index()

    def load_index(self):
        with self.fs_access_lock:
            if os.path.isfile(self.index_path):
                with open(self.index_path, 'rb') as index_file:
                    index = msgpack.unpackb(index_file.read())

                # Decode the object to utf strings except the 'hash' values
                self._index = bintools.decode_object(
                    index,
                    except_keys=('hash',)
                )

            else:
                self._index = dict()

    def save_index(self):
        index = msgpack.packb(self._index)

        with open(self.index_path, 'wb') as index_file:
            index_file.write(index)

    def update_index(self, save_index=True):
        """
        The index structure is:
            <index> ::= {
                <file_name>: <file_info>,
                ...
            }
            <file_name> ::= file path relative to directory top
            <file_info> ::= {
                'sync_log': {
                    <remote_uuid (as string)>: <timestamp>,
                    ...
                },
                'last_update_location': <remote_uuid (or the local UUID) (str)>
                'last_update': <timestamp>,
                'hash': <md5 byte-string>,
                [optional 'deleted': (True|False)]
            }
            <timestamp> ::= Datetime in unix timestamp (seconds).
                            Depends on the os time on the system on which
                            the change happened.
        """
        with self.fs_access_lock:
            for dirpath, dirnames, filenames in os.walk(self.dir_path):
                for name in filenames:
                    file_path = pathext.normalize(os.path.join(dirpath, name))
                    self._update_file_index(file_path)

            if save_index:
                self.save_index()

    def _update_file_index(self, file_path):
        relative_path = os.path.relpath(file_path, self.dir_path)
        file_data = self._index.setdefault(relative_path, dict())

        if not file_data:
            # New file
            file_hash = hash_file(file_path)
            file_data['last_update'] = int(os.path.getmtime(file_path))
            file_data['hash'] = file_hash
            file_data['last_update_location'] = self.uuid

            sync_log = file_data.setdefault('sync_log', dict())
            sync_log[self.uuid] = file_data['last_update']

        elif int(os.path.getmtime(file_path)) > file_data['last_update']:
            # Check if file is actually changed or the system time is off
            file_hash = hash_file(file_path)

            if file_data['hash'] != file_hash:
                # File modified locally (since last sync)
                file_data['last_update'] = int(os.path.getmtime(file_path))
                file_data['hash'] = file_hash
                file_data['last_update_location'] = self.uuid

                sync_log = file_data.setdefault('sync_log', dict())
                sync_log[self.uuid] = file_data['last_update']

        if 'deleted' in file_data:
            del file_data['deleted']

    def diff(self, remote_index):
        """
        Return (updates, deletes, conflicts) where
        updates, deletes and conflicts are sets of file
        names of files that need to be changed on the remote store.

        Files that need to be transferred from the remote store to the
        current one are not detected as it's handled on the remote side.

        A full two-way synchronization is handled as two separate
        one-way synchronizations (local -> remote and remote -> local).

        TODO: Support deleted files detection
        """
        updates = set()
        deletes = set()
        conflicts = set()

        for (file, file_data) in self._index.items():
            sync_status = Directory._compare_file(
                file_data,
                remote_index.get(file, None)
            )

            if sync_status == self.NEEDS_UPDATE:
                updates.add(file)
            elif sync_status == self.CONFLICT:
                conflicts.add(file)

        return (updates, deletes, conflicts)

    @staticmethod
    def _compare_file(local, remote):
        """
        Compare two files by their index data. remote can be None if remote
        data is not present.

        Return NEEDS_UPDATE if file needs to be synchronized (local -> remote),
        CONFLICT on conflict and NOT_MODIFIED otherwise.
        """
        if remote is None:
            if 'deleted' not in local or not local['deleted']:
                return Directory.NEEDS_UPDATE

        if (local['last_update_location'] in remote['sync_log'] and
                local['last_update'] <=
                remote['sync_log'][local['last_update_location']]):
            # File on remote is either the same or derived from this one
            return Directory.NOT_MODIFIED

        elif (remote['last_update_location'] in local['sync_log'] and
                remote['last_update'] <=
                local['sync_log'][remote['last_update_location']]):
            # File needs to be transferred to remote
            return Directory.NEEDS_UPDATE

        # Files are in conflict
        return Directory.CONFLICT
