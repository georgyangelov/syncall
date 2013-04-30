import unittest

from fsdiff.Directory import *


class DirectoryTests(unittest.TestCase):
    def test_diff_with(self):
        dir_one = Directory({
            'dev/python/file.py',
            'dev/python/file2.cpp',
            'dev/file.py',
            'dev/python/dir_one/file.py',
        })
        dir_two = Directory({
            'dev/python3.3/file.py',
            'dev/python/file2.cpp',
            'dev/file.py',
            'dev/python/dir_two/file.py',
            'dev/python/dir_two/file123.py',
        })

        self.assertEqual(
            dir_one.diff_with(dir_two), ({
                'dev/python3.3/file.py',
                'dev/python/dir_two/file.py',
                'dev/python/dir_two/file123.py',
            }, {
                'dev/python/file.py',
                'dev/python/dir_one/file.py',
            })
        )
