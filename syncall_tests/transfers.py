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


class TransferManagerTests(TestCase):

    @patch('logging.Logger')
    def setUp(self, Logger):
        directory = Mock()

        self.remote = MagicMock()
        self.remote.address = '127.0.0.1'
        self.messanger = MagicMock()
        self.messanger.address = ('127.0.0.1', 1234)

        self.manager = syncall.TransferManager(directory)

    def tearDown(self):
        del self.manager

    @patch('syncall.transfers.FileTransfer')
    def test_process_transfer(self, FileTransfer):
        self.manager.process_transfer(self.remote, self.messanger)

        FileTransfer.assert_called_with(self.manager.directory, self.messanger)

    def test_process_transfer_error(self):
        self.remote.address = '127.0.0.2'

        self.manager.process_transfer(self.remote, self.messanger)

        self.assertTrue(self.messanger.disconnect.called)

    @patch('syncall.Messanger.connect')
    @patch('syncall.transfers.FileTransfer')
    def test_sync_new_file(self, FileTransfer, Messanger_connect):
        remote = Mock()
        remote.address = '127.0.0.1'
        remote.my_uuid = 'my_uuid'
        remote.uuid = 'remote_uuid'

        file_transfer = MagicMock()
        FileTransfer.return_value = file_transfer

        file_transfer.get_remote_uuid.return_value = 'remote_uuid'
        file_transfer.file_name = 'file1'

        self.manager.sync_file(remote, 'file1')

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))
        self.assertTrue(
            self.manager.transfers.get('file1', 'remote_uuid').start.called
        )
        self.assertTrue(file_transfer.start.called)
        self.assertTrue(file_transfer.initialize.called)

    @patch('syncall.Messanger.connect')
    @patch('syncall.transfers.FileTransfer')
    def test_sync_file_overwrite(self, FileTransfer, Messanger_connect):
        remote = Mock()
        remote.address = '127.0.0.1'
        remote.my_uuid = 'my_uuid'
        remote.uuid = 'remote_uuid'

        file_transfer = MagicMock()
        FileTransfer.return_value = file_transfer

        file_transfer.get_remote_uuid.return_value = 'remote_uuid'
        file_transfer.file_name = 'file1'

        self.manager.sync_file(remote, 'file1')

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))

        remote2 = Mock()
        remote2.address = '127.0.0.1'
        remote2.my_uuid = 'my_uuid'
        remote2.uuid = 'remote_uuid'

        file_transfer2 = MagicMock()
        FileTransfer.return_value = file_transfer2

        file_transfer2.get_remote_uuid.return_value = 'remote_uuid'
        file_transfer2.file_name = 'file1'
        file_transfer2.file_data = {
            'last_update': 1234
        }
        self.manager.directory.get_index.return_value = {
            'file1': {
                'last_update': 234
            }
        }

        self.manager.sync_file(remote2, 'file1')

        self.assertTrue(file_transfer.shutdown.called)
        self.assertTrue(file_transfer2.initialize.called)
        self.assertTrue(file_transfer2.start.called)

    def test_new_transfer_started_handler(self):
        transfer = Mock()
        transfer.get_remote_uuid.return_value = 'remote_uuid'
        transfer.file_name = 'file1'

        self.manager._TransferManager__transfer_started(transfer)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))

    @patch('syncall.IndexDiff.compare_file')
    def test_transfer_started_handler_newer(self, compare_file):
        transfer = Mock()
        transfer.get_remote_uuid.return_value = 'remote_uuid'
        transfer.file_name = 'file1'

        self.manager._TransferManager__transfer_started(transfer)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))

        transfer2 = Mock()
        transfer2.get_remote_uuid.return_value = 'remote_uuid'
        transfer2.file_name = 'file1'
        compare_file.return_value = syncall.index.NEEDS_UPDATE

        self.manager._TransferManager__transfer_started(transfer2)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))
        self.assertTrue(transfer.shutdown.called)

    @patch('syncall.IndexDiff.compare_file')
    def test_transfer_started_handler_older(self, compare_file):
        transfer = Mock()
        transfer.get_remote_uuid.return_value = 'remote_uuid'
        transfer.file_name = 'file1'

        self.manager._TransferManager__transfer_started(transfer)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))

        transfer2 = Mock()
        transfer2.get_remote_uuid.return_value = 'remote_uuid'
        transfer2.file_name = 'file1'
        compare_file.return_value = syncall.index.NOT_MODIFIED

        self.manager._TransferManager__transfer_started(transfer2)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))
        self.assertTrue(transfer2.shutdown.called)

        compare_file.return_value = syncall.index.CONFLICT
        transfer2.shutdown.called = False

        self.manager._TransferManager__transfer_started(transfer2)

        self.assertTrue(self.manager.transfers.has('file1', 'remote_uuid'))
        self.assertTrue(transfer2.shutdown.called)

    def test_transfer_completed_handler(self):
        transfer = Mock()
        self.manager.transfers = Mock()

        self.manager._TransferManager__transfer_completed(transfer)

        self.manager.transfers.remove.assert_called_with(transfer)

    def test_transfer_failed_handler(self):
        transfer = Mock()
        self.manager.transfers = Mock()

        self.manager._TransferManager__transfer_failed(transfer)

        self.manager.transfers.remove.assert_called_with(transfer)

    def test_transfer_cancelled_handler(self):
        transfer = Mock()
        self.manager.transfers = Mock()

        self.manager._TransferManager__transfer_cancelled(transfer)

        self.manager.transfers.remove.assert_called_with(transfer)

    def test_sync_files(self):
        remote = Mock()
        file_list = {'file1', 'file2'}

        self.manager.sync_file = Mock()
        self.manager.sync_files(remote, file_list)

        for file in file_list:
            self.manager.sync_file.assert_any_call(remote, file)

    def test_stop_transfers(self):
        self.manager.transfers = Mock()
        self.manager.transfers.get_all.return_value = [
            Mock(), Mock(), Mock()
        ]

        self.manager.stop_transfers()

        for transfer in self.manager.transfers.get_all():
            self.assertTrue(transfer.shutdown.called)

    def test_remote_disconnect(self):
        transfer_remote1 = Mock()
        transfer_remote1.get_remote_uuid.return_value = 'uuid1'

        transfer_remote2 = Mock()
        transfer_remote2.get_remote_uuid.return_value = 'uuid2'

        transfer_remote3 = Mock()
        transfer_remote3.get_remote_uuid.return_value = 'uuid1'

        self.manager.transfers = Mock()
        self.manager.transfers.get_all.return_value = [
            transfer_remote1, transfer_remote2, transfer_remote3
        ]

        remote = Mock()
        remote.uuid = 'uuid1'

        self.manager.remote_disconnect(remote)

        self.assertTrue(transfer_remote1.shutdown.called)
        self.assertFalse(transfer_remote2.shutdown.called)
        self.assertTrue(transfer_remote3.shutdown.called)
