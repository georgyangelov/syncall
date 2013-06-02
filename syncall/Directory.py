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
    def __init__(self, dir_path, index_name='.syncall_index'):
        self.logger = logging.getLogger(__name__)

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
                    <remote_uuid in UTF>: <remote_sync_info>,
                    ...
                },
                'last_update': <datetime in unix timestamp (seconds)>,
                'hash': <md5 byte-string>,
                [optional 'deleted': (True|False)]
            }
            <remote_sync_info> ::= {
                'last_update': <datetime in unix timestamp>,
                'hash': <md5 byte-string>
            }
        """
        with self.fs_access_lock:
            for dirpath, dirnames, filenames in os.walk(self.dir_path):
                for name in filenames:
                    file_path = pathext.normalize(os.path.join(dirpath, name))
                    self._update_index_file(file_path)

            self.save_index()

    def _update_index_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.dir_path)
        file_data = self._index.setdefault(relative_path, dict())

        file_data['last_update'] = int(os.path.getmtime(file_path))
        file_data['hash'] = hash_file(file_path)

        if 'deleted' in file_data:
            del file_data['deleted']
