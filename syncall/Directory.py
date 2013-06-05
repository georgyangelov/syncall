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

    def get_index(self):
        return self._index

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
                'hash': <md5 byte-string | 0x0...0 if file is deleted>
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

        return self._index

    def _update_index_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.dir_path)
        file_data = self._index.setdefault(relative_path, dict())

        file_data['last_update'] = int(os.path.getmtime(file_path))
        file_data['hash'] = hash_file(file_path)


class FileIndexChanges:
    """
    Computes and holds the changes that are required to synchronize 2
    file sets.
    """

    def __init__(self, index_from, index_to, uuid_to):
        self.index_from = index_from
        self.index_to = index_to
        self.uuid_to = to_uuid

    def get_diff(self):
        """
        Compute the changes required to sync `self._from` and `self._to`.
        Files in `from` are NOT neccesarily in `to`'s history. They can be
        different branches.

        Return tuple with 4 sets of file names: (
            added      [keys from self._to],
            removed    [keys from self._from],
            modified   [keys from self._to and self._from],
            conflicted [keys from self._to and self._from]
        )

        Conflicted are files which are modified on both remotes and may not
        neccesarily have common history.
        """

        # TODO: This is not the way it's supposed to work
        # We're not certain that from is in to's history
        # This needs a complete rewrite
        added = set()
        removed = set()
        modified = set()
        conflicted = set()

        for file in self.index_to:
            if file not in self.index_from:
                # Added file
                added.add(file)
            else:
                # Not modified, Modified or Conflicted
                if self.index_from[file]['hash'] !=
                self.index_to[file]['hash']:
                    # Modified or Conflicted
                    pass

        for file in self.index_from:
            if file not in self.index_to:
                # Removed file
                removed.add(file)
