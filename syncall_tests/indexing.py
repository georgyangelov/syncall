import unittest
import os
import time

from unittest.mock import Mock, patch

import bintools
import syncall


class DirectoryIndexTests(unittest.TestCase):
    TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/test_files'

    TEST_FILES = (
        'README.txt',
        'animals/README.txt',
        'animals/cat.jpg',
        'animals/dogs/dog.jpg'
    )

    @patch('logging.Logger')
    def setUp(self, Logger):
        self.directory = syncall.Directory(
            'uuid',
            self.TEST_DIR,
            load_index=False,
            temp_dir_name='.syncall_temp',
            create_temp_dir=False
        )

    def tearDown(self):
        del self.directory

        try:
            os.remove(self.TEST_DIR + '/.syncall_index')
        except:
            pass

        try:
            os.remove(self.TEST_DIR + '/animals/added_file.txt')
        except:
            pass

    @patch("os.mkdir")
    def test_create_temp_dir(self, mkdir):
        directory = syncall.Directory(
            'uuid',
            self.TEST_DIR,
            temp_dir_name='.syncall_temp',
            create_temp_dir=True,
            load_index=False
        )

        mkdir.assert_called_with(
            os.path.join(self.TEST_DIR, '.syncall_temp')
        )

    @patch("os.remove")
    @patch("os.path.isfile", side_effect=[True, True, False])
    @patch("builtins.open")
    def test_temp_files(self, open, isfile, remove):
        res = self.directory.get_temp_path('test')
        expected = os.path.join(
            self.TEST_DIR, '.syncall_temp', 'test-2'
        )

        self.assertEqual(res, expected)
        open.assert_called_with(expected, 'a+')

        isfile.side_effect = [True]
        self.directory.clear_temp_dir()
        remove.assert_called_once_with(expected)

    def test_get_file_path(self):
        res = self.directory.get_file_path('test')

        self.assertEqual(res, os.path.join(self.TEST_DIR, 'test'))

    @patch("pyrsync2.blockchecksums")
    @patch("builtins.open")
    def test_get_block_checksums(self, open, blockchecksums):
        blockchecksums.return_value = [1, 2, 3]
        hashes = self.directory.get_block_checksums('test', 1024)

        self.assertFalse(open.called)
        self.assertFalse(blockchecksums.called)
        self.assertEqual(len(hashes), 0)

        self.directory._index['test'] = {
            'deleted': True
        }
        hashes = self.directory.get_block_checksums('test', 1024)

        self.assertFalse(open.called)
        self.assertFalse(blockchecksums.called)
        self.assertEqual(len(hashes), 0)

        self.directory._index['test'] = dict()
        hashes = self.directory.get_block_checksums('test', 1024)

        open.assert_called_with(self.directory.get_file_path('test'), 'rb')

        self.assertEqual(hashes, [1, 2, 3])

    def test_get_index(self):
        self.directory._index = {
            'file': {
                'test': True
            }
        }

        self.assertEqual(self.directory.get_index(), self.directory._index)
        self.assertIsNone(self.directory.get_index('no_file'))
        self.assertEqual(
            self.directory.get_index('file'),
            self.directory._index['file']
        )

    def test_new_index(self):
        self.directory.update_index(save_index=True)

        for path in self.TEST_FILES:
            self.assertIn(path, self.directory._index)

            file_data = self.directory._index[path]
            self.assertIn('last_update', file_data)
            self.assertIn('last_update_location', file_data)
            self.assertEqual(file_data['last_update_location'], 'uuid')
            self.assertIn('hash', file_data)
            self.assertIn('sync_log', file_data)
            self.assertIn('uuid', file_data['sync_log'])
            self.assertEqual(
                file_data['sync_log']['uuid'],
                file_data['last_update']
            )

        self.assertTrue(os.path.exists(self.TEST_DIR + '/.syncall_index'))

    def test_load_index(self):
        directory = syncall.Directory('uuid', self.TEST_DIR)
        directory.update_index(save_index=True)

        del directory

        directory = syncall.Directory('uuid', self.TEST_DIR)

        for path in self.TEST_FILES:
            self.assertIn(path, directory._index)

            file_data = directory._index[path]
            self.assertIn('last_update', file_data)
            self.assertIn('last_update_location', file_data)
            self.assertEqual(file_data['last_update_location'], 'uuid')
            self.assertIn('hash', file_data)
            self.assertEqual(
                file_data['hash'],
                bintools.hash_file(self.TEST_DIR + '/' + path)
            )
            self.assertIn('sync_log', file_data)
            self.assertIn('uuid', file_data['sync_log'])
            self.assertEqual(
                file_data['sync_log']['uuid'],
                file_data['last_update']
            )

    def test_same_file(self):
        self.directory.update_index(save_index=True)

        readme_file = self.TEST_DIR + '/README.txt'
        readme_file_data = self.directory._index['README.txt']
        old_last_update = self.directory._index['README.txt']['last_update']

        readme_file_data['deleted'] = True

        # Make sure modification times are different
        time.sleep(1)

        # Touch the readme file
        os.utime(readme_file, None)

        self.directory.uuid = 'uuid_new'
        self.directory.update_index(save_index=False)

        # File shouldn't be detected as changed if hashes are the same
        self.assertEqual(readme_file_data['last_update'], old_last_update)
        self.assertEqual(readme_file_data['last_update_location'], 'uuid')
        self.assertIn('uuid', readme_file_data['sync_log'])
        self.assertEqual(
            readme_file_data['sync_log']['uuid'],
            readme_file_data['last_update']
        )

    def test_modified_file(self):
        added_file = self.TEST_DIR + '/animals/added_file.txt'
        readme_file = self.TEST_DIR + '/animals/README.txt'

        with open(readme_file, 'w') as file:
            file.write("test content v1")

        self.directory.update_index(save_index=False)

        readme_file_data = self.directory._index['animals/README.txt']
        old_last_update = \
            self.directory._index['animals/README.txt']['last_update']

        # Make sure the modification times differ
        time.sleep(1)

        # Update the readme file
        with open(readme_file, 'w') as file:
            file.write("test content v2 with some mods")

        with open(added_file, 'w') as file:
            file.write("added file content")

        self.directory.uuid = 'uuid_new'
        self.directory.update_index(save_index=False)

        self.assertEqual(readme_file_data['last_update_location'], 'uuid_new')
        self.assertGreater(readme_file_data['last_update'], old_last_update)
        self.assertIn('uuid_new', readme_file_data['sync_log'])
        self.assertEqual(
            readme_file_data['sync_log']['uuid_new'],
            readme_file_data['last_update']
        )

        self.assertIn('animals/added_file.txt', self.directory._index)

    @patch('os.walk')
    def test_deleted_file(self, walk):
        walk.return_value = []

        self.directory._index['animals/README.txt'] = {
            'last_update': 123,
            'last_update_location': 'uuid',
        }
        old_file_data = self.directory._index['animals/README.txt']

        old_last_update = old_file_data['last_update']
        old_uuid = old_file_data['last_update_location']

        self.directory.uuid = 'uuid_new'
        self.directory.update_index(save_index=False)

        readme_file_data = self.directory._index['animals/README.txt']

        self.directory.update_index(save_index=False)

        self.assertEqual(readme_file_data['last_update_location'], 'uuid_new')
        self.assertGreater(readme_file_data['last_update'], old_last_update)
        self.assertTrue(readme_file_data['deleted'])
        self.assertIn('uuid_new', readme_file_data['sync_log'])
        self.assertEqual(
            readme_file_data['sync_log']['uuid_new'],
            readme_file_data['last_update']
        )

    def test_finalize_transfer_to_remote(self):
        transfer = Mock()
        transfer.type = syncall.transfers.FileTransfer.TO_REMOTE
        transfer.file_name = 'file1'
        transfer.get_remote_uuid.return_value = 'uuid2'
        transfer.timestamp = 1250

        self.directory.last_update = 123
        self.directory.save_index = Mock()
        self.directory.index_updated = Mock()
        self.directory._index['file1'] = {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1000
            }
        }

        self.directory.finalize_transfer(transfer)

        self.assertGreater(self.directory.last_update, 123)
        self.assertEqual(self.directory._index['file1'], {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1250
            }
        })
        self.directory.index_updated.notify.assert_called_once_with(
            {'file1'}
        )
        self.assertTrue(self.directory.save_index.called)

    @patch('shutil.move')
    @patch('syncall.index.IndexDiff.compare_file')
    def test_finalize_transfer_from_remote(self, compare_file, move):
        transfer = Mock()
        transfer.type = syncall.transfers.FileTransfer.FROM_REMOTE
        transfer.file_name = 'file1'
        transfer.messanger.my_uuid = 'uuid2'
        transfer.timestamp = 1250
        transfer.get_temp_path.return_value = '/temp/file1'
        transfer.remote_file_data = {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1000
            }
        }

        compare_file.return_value = syncall.index.NEEDS_UPDATE

        self.directory.get_file_path = Mock()
        self.directory.get_file_path.return_value = '/dir/file1'

        self.directory.last_update = 123
        self.directory.save_index = Mock()
        self.directory.index_updated = Mock()

        self.directory.finalize_transfer(transfer)

        self.assertGreater(self.directory.last_update, 123)
        self.assertEqual(self.directory._index['file1'], {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1250
            }
        })
        self.directory.index_updated.notify.assert_called_once_with(
            {'file1'}
        )
        self.assertTrue(self.directory.save_index.called)

    @patch('os.remove')
    @patch('syncall.index.IndexDiff.compare_file')
    def test_finalize_transfer_from_remote_deleted(self, compare_file, remove):
        transfer = Mock()
        transfer.type = syncall.transfers.FileTransfer.FROM_REMOTE
        transfer.file_name = 'file1'
        transfer.messanger.my_uuid = 'uuid2'
        transfer.timestamp = 1250
        transfer.get_temp_path.return_value = '/temp/file1'
        transfer.remote_file_data = {
            'last_update': 1234,
            'deleted': True,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1000
            }
        }

        compare_file.return_value = syncall.index.NEEDS_UPDATE

        self.directory.get_file_path = Mock()
        self.directory.get_file_path.return_value = '/dir/file1'

        self.directory.last_update = 123
        self.directory.save_index = Mock()
        self.directory.index_updated = Mock()

        self.directory.finalize_transfer(transfer)

        self.assertGreater(self.directory.last_update, 123)
        self.assertEqual(self.directory._index['file1'], {
            'last_update': 1234,
            'deleted': True,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1250
            }
        })
        self.directory.index_updated.notify.assert_called_once_with(
            {'file1'}
        )
        remove.assert_called_once_with(
            self.directory.get_file_path(transfer.file_name)
        )
        self.assertTrue(self.directory.save_index.called)

    @patch('syncall.index.IndexDiff.compare_file')
    def test_finalize_transfer_from_remote_old(self, compare_file):
        transfer = Mock()
        transfer.type = syncall.transfers.FileTransfer.FROM_REMOTE
        transfer.file_name = 'file1'

        compare_file.return_value = syncall.index.CONFLICT

        self.directory.get_file_path = Mock()
        self.directory.get_file_path.return_value = '/dir/file1'

        self.directory.last_update = 123
        self.directory.save_index = Mock()
        self.directory.index_updated = Mock()
        self.directory._index['file1'] = {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1000
            }
        }

        self.directory.finalize_transfer(transfer)

        self.assertEqual(self.directory.last_update, 123)
        self.assertEqual(self.directory._index['file1'], {
            'last_update': 1234,
            'sync_log': {
                'my_uuid': 1234,
                'uuid1': 1200,
                'uuid2': 1000
            }
        })
        self.assertFalse(self.directory.index_updated.notify.called)
        self.assertTrue(self.directory.save_index.called)
