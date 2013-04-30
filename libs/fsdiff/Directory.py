import os
import pathext


class Directory:
    def __init__(self, files=None):
        if files is not None:
            self.files = files
        else:
            self.files = set()

    @staticmethod
    def from_fs(path):
        """
        Create and return a Directory instance with data from the filesystem
        """
        files = set()

        for dirpath, dirnames, filenames in os.walk(path):
            for name in filenames:
                files.add(pathext.normalize(os.path.join(dirpath, name)))

        return Directory(files)

    def diff_with(self, other):
        """
        Return tuple (set of added_files, set of removed_files) based on
        the difference between `self` and `other`.

        If a file is in `self` but not in `other` then it will be in the
        `removed_files` set.
        """
        added_files = other.files - self.files
        rm_files = self.files - other.files

        return (added_files, rm_files)
