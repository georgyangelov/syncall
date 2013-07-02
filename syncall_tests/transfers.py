from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

import syncall


class TransferDictTests(TestCase):
    def setUp(self):
        self.dict = syncall.transfers.TransferDict()

    def tearDown(self):
        del self.dict

    def test_add_contains(self):
        transfer = Mock()
        transfer.file_name = 'file1'
        transfer.get_remote_uuid.return_value = 'uuid1'

        self.dict.add(transfer)

        self.assertTrue(self.dict.has('file1', 'uuid1'))
        self.assertEqual(self.dict.get('file1', 'uuid1'), transfer)

        transfer2 = Mock()
        transfer2.file_name = 'file1'
        transfer2.get_remote_uuid.return_value = 'uuid1'

        self.assertTrue(self.dict.has_same(transfer2))
        self.assertEqual(self.dict.get_same(transfer2), transfer)
        self.assertTrue(self.dict.has_transfers('file1'))

        self.assertFalse(self.dict.has_transfers('file2'))

    def test_multiple_transfers(self):
        transfer1 = Mock()
        transfer1.file_name = 'file1'
        transfer1.get_remote_uuid.return_value = 'uuid1'

        transfer2 = Mock()
        transfer2.file_name = 'file1'
        transfer2.get_remote_uuid.return_value = 'uuid2'

        self.dict.add(transfer1)
        self.dict.add(transfer2)

        self.assertEqual(len(self.dict.get_transfers('file1')), 2)
        self.assertEqual(self.dict.get_same(transfer1), transfer1)
        self.assertEqual(self.dict.get_same(transfer2), transfer2)
        self.assertEqual(
            set(self.dict.get_all()),
            {transfer1, transfer2}
        )

    def test_remove(self):
        transfer1 = Mock()
        transfer1.file_name = 'file1'
        transfer1.get_remote_uuid.return_value = 'uuid1'

        self.dict.add(transfer1)
        self.dict.remove(transfer1)

        self.assertFalse(self.dict.has_same(transfer1))

        self.dict.remove(transfer1)
