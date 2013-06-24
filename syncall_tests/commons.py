import unittest
import uuid
import io

import syncall


class CommonsTests(unittest.TestCase):

    @unittest.mock.patch("builtins.open")
    def test_generate_uuid(self, open):
        file = io.StringIO()
        open.return_value = file

        my_uuid = syncall.generate_uuid("file_test")

        open.assert_called_with("file_test", "w")

        uuid.UUID(my_uuid)

    @unittest.mock.patch("os.path.isfile")
    @unittest.mock.patch("builtins.open")
    def test_get_uuid(self, open, isfile):
        isfile.return_value = True

        f = io.StringIO('test_uuid')
        open.return_value = f

        my_uuid = syncall.get_uuid('file_test')

        open.assert_called_with("file_test", "r")
        self.assertEqual('test_uuid', my_uuid)

    @unittest.mock.patch("os.path.isfile")
    @unittest.mock.patch("syncall.commons.generate_uuid")
    def test_get_generate_uuid(self, gen, isfile):
        gen.return_value = "1234"
        isfile.return_value = False

        self.assertEqual(syncall.get_uuid('file_test'), "1234")
