import unittest
import os
import time

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

    def tearDown(self):
        try:
            os.remove(self.TEST_DIR + '/.syncall_index')
        except:
            pass

        try:
            os.remove(self.TEST_DIR + '/animals/added_file.txt')
        except:
            pass

    def test_new_index(self):
        directory = syncall.Directory('uuid', self.TEST_DIR)
        directory.update_index(save_index=True)

        for path in self.TEST_FILES:
            self.assertIn(path, directory._index)

            file_data = directory._index[path]
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
        os.remove(self.TEST_DIR + '/.syncall_index')

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

        os.remove(self.TEST_DIR + '/.syncall_index')

    def test_same_file(self):
        directory = syncall.Directory('uuid', self.TEST_DIR)
        directory.update_index(save_index=True)

        readme_file = self.TEST_DIR + '/README.txt'
        readme_file_data = directory._index['README.txt']
        old_last_update = directory._index['README.txt']['last_update']

        readme_file_data['deleted'] = True

        # Make sure modification times are different
        time.sleep(1)

        # Touch the readme file
        os.utime(readme_file, None)

        directory.uuid = 'uuid_new'
        directory.update_index(save_index=False)

        # File shouldn't be detected as changed if hashes are the same
        self.assertEqual(readme_file_data['last_update'], old_last_update)
        self.assertEqual(readme_file_data['last_update_location'], 'uuid')
        self.assertIn('uuid', readme_file_data['sync_log'])
        self.assertEqual(
            readme_file_data['sync_log']['uuid'],
            readme_file_data['last_update']
        )

        os.remove(self.TEST_DIR + '/.syncall_index')

    def test_modified_file(self):
        added_file = self.TEST_DIR + '/animals/added_file.txt'
        readme_file = self.TEST_DIR + '/animals/README.txt'

        with open(readme_file, 'w') as file:
            file.write("test content v1")

        directory = syncall.Directory('uuid', self.TEST_DIR)
        directory.update_index(save_index=False)

        readme_file_data = directory._index['animals/README.txt']
        old_last_update = directory._index['animals/README.txt']['last_update']

        # Make sure the modification times differ
        time.sleep(1)

        # Update the readme file
        with open(readme_file, 'w') as file:
            file.write("test content v2 with some mods")

        with open(added_file, 'w') as file:
            file.write("added file content")

        directory.uuid = 'uuid_new'
        directory.update_index(save_index=False)

        self.assertEqual(readme_file_data['last_update_location'], 'uuid_new')
        self.assertGreater(readme_file_data['last_update'], old_last_update)
        self.assertIn('uuid_new', readme_file_data['sync_log'])
        self.assertEqual(
            readme_file_data['sync_log']['uuid_new'],
            readme_file_data['last_update']
        )

        self.assertIn('animals/added_file.txt', directory._index)

        os.remove(self.TEST_DIR + '/animals/added_file.txt')
