import unittest

import syncall


class IndexDiffTests(unittest.TestCase):

    def assertDiff(self, diff, updates, deletes, conflicts):
        self.assertEqual(diff[0], updates)
        self.assertEqual(diff[1], deletes)
        self.assertEqual(diff[2], conflicts)

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
        self.assertDiff(diffAB, {'dir/file1'}, set(), set())

        diffBA = self.dirB.diff(self.dirA._index)
        self.assertDiff(diffBA, set(), set(), set())

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
        self.assertDiff(diffAB, set(), set(), set())

        diffBA = self.dirB.diff(self.dirA._index)
        self.assertDiff(diffBA, {'dir/file1'}, set(), set())

    def test_conflict_simple(self):
        self.dirA._index = {
            'dir/file1': {
                'last_update': 5,
                'last_update_location': 'A',
                'hash': 'A5',
                'sync_log': {
                    'A': 5
                }
            }
        }
        self.dirB._index = {
            'dir/file1': {
                'last_update': 6,
                'last_update_location': 'B',
                'hash': 'B6',
                'sync_log': {
                    'B': 6
                }
            }
        }

        diffAB = self.dirA.diff(self.dirB._index)
        self.assertDiff(diffAB, set(), set(), {'dir/file1'})

        diffBA = self.dirB.diff(self.dirA._index)
        self.assertDiff(diffBA, set(), set(), {'dir/file1'})
