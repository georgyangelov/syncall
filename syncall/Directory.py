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
    def __init__(self, uuid, dir_path, index_name='.syncall_index'):
        self.logger = logging.getLogger(__name__)

        self.uuid = uuid
        self.dir_path = dir_path
        self.index_name = index_name
        self.index_path = os.path.join(self.dir_path, self.index_name)

        self.fs_access_lock = threading.Lock()

        self._load_index()

    def _load_index(self):
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

    def update_index(self):
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

        elif file_data['last_update'] > int(os.path.getmtime(file_path)):
            # Check if file is actually changed or the system time is off
            file_hash = hash_file(file_path)

            if file_data['hash'] != file_hash:
                # File modified locally (since last sync)
                file_data['last_update'] = int(os.path.getmtime(file_path))
                file_data['hash'] = file_hash
                file_data['last_update_location'] = self.uuid

        if 'deleted' in file_data:
            del file_data['deleted']
