import unittest

import syncall


class IndexDiffTests(unittest.TestCase):

    def setUp(self):
        self.dirA = syncall.Directory('A', 'dummy_dir', load_index=False)
        self.dirB = syncall.Directory('B', 'dummy_dir', load_index=False)

    def test_new_file(self):
        self.dirA._index = {
            'dir/file1': {
                'last_update': 10,
                'last_update_location': 'A',
                'hash': 'A10',
                'sync_log': {
                    'A': 10
                }
            }
        }
        self.dirB._index = {}

        diffAB = self.dirA.diff(self.dirB._index)
        self.assertEqual(diffAB[0], {
            'dir/file1'
        })
        self.assertEqual(diffAB[1], set())
        self.assertEqual(diffAB[2], set())

        diffBA = self.dirB.diff(self.dirA._index)
        self.assertEqual(diffBA[0], set())
        self.assertEqual(diffBA[1], set())
        self.assertEqual(diffBA[2], set())

    def test_modified_file_simple(self):
        self.dirA._index = {
            'dir/file1': {
                'last_update': 1,
                'last_update_location': 'A',
                'hash': 'A1',
                'sync_log': {
                    'A': 1
                }
            }
        }
        self.dirB._index = {
            'dir/file1': {
                'last_update': 10,
                'last_update_location': 'B',
                'hash': 'B10',
                'sync_log': {
                    'A': 5,
                    'B': 10
                }
            }
        }

        diffAB = self.dirA.diff(self.dirB._index)
        self.assertEqual(diffAB[0], set())
        self.assertEqual(diffAB[1], set())
        self.assertEqual(diffAB[2], set())

        diffBA = self.dirB.diff(self.dirA._index)
        self.assertEqual(diffBA[0], {
            'dir/file1'
        })
        self.assertEqual(diffBA[1], set())
        self.assertEqual(diffBA[2], set())
