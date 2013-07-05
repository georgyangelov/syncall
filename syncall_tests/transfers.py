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
        transfer.type = syncall.transfers.FileTransfer.TO_REMOTE

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
        transfer1.type = syncall.transfers.FileTransfer.TO_REMOTE

        transfer2 = Mock()
        transfer2.file_name = 'file1'
        transfer2.get_remote_uuid.return_value = 'uuid2'
        transfer2.type = syncall.transfers.FileTransfer.TO_REMOTE

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
        transfer1.type = syncall.transfers.FileTransfer.TO_REMOTE

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


class FileTransferNotStartedTests(TestCase):

    @patch('logging.Logger')
    def setUp(self, Logger):
        directory = MagicMock()
        directory.get_index.return_value = {
            'last_update': 123
        }

        messanger = MagicMock()
        messanger.remote_uuid = 'remote_uuid'

        self.transfer = syncall.transfers.FileTransfer(
            directory,
            messanger,
            file_name='file1'
        )

    def tearDown(self):
        del self.transfer

    def test_initialize(self):
        self.transfer.initialize()
        self.assertTrue(self.transfer.messanger.start_receiving.called)

    def test_is_done(self):
        self.assertFalse(self.transfer.is_done())

    def test_has_started(self):
        self.assertFalse(self.transfer.has_started())

    def test_get_remote_uuid(self):
        self.assertEqual(self.transfer.get_remote_uuid(), 'remote_uuid')

    def test_shutdown(self):
        self.transfer.transfer_cancelled = MagicMock()

        self.transfer.shutdown()

        self.assertTrue(self.transfer.transfer_cancelled.notify.called)
        self.assertTrue(self.transfer.messanger.disconnect.called)
        self.assertTrue(self.transfer.is_done())

    def test_terminate(self):
        self.transfer.transfer_cancelled = MagicMock()
        self.transfer.transfer_completed = MagicMock()
        self.transfer.transfer_failed = MagicMock()

        self.transfer.terminate()

        self.assertFalse(self.transfer.transfer_cancelled.called)
        self.assertFalse(self.transfer.transfer_completed.called)
        self.assertFalse(self.transfer.transfer_failed.called)

        self.assertTrue(self.transfer.messanger.disconnect.called)

    def test_data_packet_received(self):
        self.transfer.terminate = Mock()
        self.transfer._FileTransfer__data_received = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_BLOCK_DATA,
            'binary_data': 'test'
        })

        self.assertTrue(self.transfer.terminate.called)
        self.assertFalse(self.transfer._FileTransfer__data_received.called)

    def test_unknown_packet_received(self):
        self.transfer._FileTransfer__packet_received({
            'type': 999
        })

    def test_release_resources_no_error(self):
        # No error
        self.transfer._FileTransfer__release_resources()

    def test_release_resources(self):
        tmp_handle = self.transfer._FileTransfer__temp_file_handle = Mock()
        file_handle = self.transfer._FileTransfer__file_handle = Mock()
        tmp_name = self.transfer._FileTransfer__temp_file_name = Mock()

        self.transfer._FileTransfer__release_resources()

        self.assertTrue(tmp_handle.close.called)
        self.assertTrue(file_handle.close.called)
        self.transfer.directory.release_temp_file.assert_called_once_with(
            tmp_name
        )

        self.assertIsNone(self.transfer._FileTransfer__temp_file_handle)
        self.assertIsNone(self.transfer._FileTransfer__file_handle)
        self.assertIsNone(self.transfer._FileTransfer__temp_file_name)


class FileTransferSendTests(TestCase):

    @patch('threading.Thread')
    @patch('logging.Logger')
    def setUp(self, Logger, Thread):
        directory = MagicMock()
        directory.get_index.return_value = {
            'last_update': 123
        }

        messanger = MagicMock()
        messanger.remote_uuid = 'remote_uuid'

        self.transfer = syncall.transfers.FileTransfer(
            directory,
            messanger,
            file_name='file1'
        )

    def tearDown(self):
        del self.transfer

    def test_type(self):
        self.assertEqual(self.transfer.type, self.transfer.TO_REMOTE)

    def test_file_data(self):
        self.assertEqual(self.transfer.file_data, {
            'last_update': 123
        })

    def test_start(self):
        self.transfer.transfer_started = MagicMock()

        self.transfer.start()

        self.assertTrue(self.transfer.transfer_started.notify.called)
        self.transfer.messanger.send.assert_called_once_with({
            'type': self.transfer.MSG_INIT,
            'name': 'file1',
            'data': {
                'last_update': 123
            }
        })
        self.assertTrue(self.transfer.has_started())

    def test_transfer_file(self):
        self.transfer.run = Mock()
        self.transfer._FileTransfer__transfer_file(
            [(1234, b'12345'), (1234, b'12345')],
            256
        )

        self.assertEqual(self.transfer.block_size, 256)
        self.assertEqual(
            self.transfer.remote_checksums,
            [(1234, b'12345'), (1234, b'12345')]
        )
        self.assertTrue(self.transfer.run.called)

    @patch('pyrsync2.rsyncdelta')
    @patch('builtins.open')
    def test_run(self, open, rsyncdelta):
        delta = [
            1, 2, 3, 4, 5, b'sdfjksdf', 7, 6, b'1234'
        ]
        rsyncdelta.return_value = delta

        self.transfer.run()

        for block in delta:
            self.transfer.messanger.send.assert_any_call({
                'type': self.transfer.MSG_BLOCK_DATA,
                'binary_data': block
            })

        self.transfer.messanger.send.assert_called_with({
            'type': self.transfer.MSG_DONE
        })

    @patch('pyrsync2.rsyncdelta')
    @patch('builtins.open')
    def test_run_error(self, open, rsyncdelta):
        rsyncdelta.side_effect = OSError()
        self.transfer.shutdown = Mock()

        self.transfer.run()

        self.assertTrue(self.transfer.shutdown.called)

    def test_packet_received_init_accept(self):
        self.transfer._FileTransfer__transfer_file = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_INIT_ACCEPT,
            'checksums': [(1234, b'12345'), (1234, b'12345')],
            'block_size': 128
        })

        self.transfer._FileTransfer__transfer_file.assert_called_once_with(
            [(1234, b'12345'), (1234, b'12345')],
            128
        )

    def test_packet_received_init_accept_delete(self):
        self.transfer._FileTransfer__transfer_file = Mock()
        self.transfer.is_delete = Mock(return_value=True)

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_INIT_ACCEPT
        })

        self.transfer.messanger.send.assert_called_once_with({
            'type': self.transfer.MSG_DONE
        })

    def test_packet_received_done_accept(self):
        self.transfer.transfer_completed = Mock()
        self.transfer.terminate = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_DONE_ACCEPT,
            'time': 128
        })

        self.assertTrue(self.transfer.is_done())
        self.assertEqual(self.transfer.timestamp, 128)
        self.assertTrue(self.transfer.terminate.called)
        self.transfer.transfer_completed.notify.assert_called_once_with(
            self.transfer
        )


class FileTransferReceiveTests(TestCase):

    @patch('threading.Thread')
    @patch('logging.Logger')
    def setUp(self, Logger, Thread):
        directory = MagicMock()
        directory.get_index.return_value = {
            'last_update': 123
        }

        messanger = MagicMock()
        messanger.remote_uuid = 'remote_uuid'

        self.transfer = syncall.transfers.FileTransfer(
            directory,
            messanger
        )

    def tearDown(self):
        del self.transfer

    @patch('syncall.IndexDiff.compare_file')
    def test_accept_file_no_update(self, compare_file):
        compare_file.return_value = syncall.index.NOT_MODIFIED
        self.transfer.shutdown = Mock()

        self.transfer._FileTransfer__accept_file('file1', {
            'last_update': 123
        })

        self.assertTrue(self.transfer.shutdown.called)

    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('syncall.IndexDiff.compare_file')
    def test_accept_file(self, compare_file, open, exists):
        compare_file.return_value = syncall.index.NEEDS_UPDATE
        exists.return_value = False
        self.transfer.directory.get_index.return_value = {
            'last_update': 100
        }
        self.transfer.directory.get_temp_path.return_value = '/tmp/file1'
        self.transfer.directory.get_block_checksums.return_value = [
            (1234, b'12345'),
            (1234, b'12345')
        ]
        self.transfer.transfer_started = Mock()
        self.transfer.block_size = 123

        self.transfer._FileTransfer__accept_file('file1', {
            'last_update': 123
        })

        self.assertTrue(self.transfer.transfer_started.notify.called)
        self.assertEqual(self.transfer.file_name, 'file1')
        self.assertEqual(self.transfer.file_data, {
            'last_update': 100
        })
        self.assertEqual(self.transfer.remote_file_data, {
            'last_update': 123
        })
        self.assertEqual(
            self.transfer._FileTransfer__temp_file_name,
            '/tmp/file1'
        )

        self.transfer.messanger.send.assert_called_once_with({
            'type': self.transfer.MSG_INIT_ACCEPT,
            'block_size': self.transfer.block_size,
            'checksums': [
                (1234, b'12345'),
                (1234, b'12345')
            ]
        })

        exists.return_value = True
        self.transfer._FileTransfer__accept_file('file1', {
            'last_update': 123
        })

    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('syncall.IndexDiff.compare_file')
    def test_accept_file_delete(self, compare_file, open, exists):
        compare_file.return_value = syncall.index.NEEDS_UPDATE
        exists.return_value = False
        self.transfer.directory.get_index.return_value = {
            'last_update': 100,
        }
        self.transfer.transfer_started = Mock()

        self.transfer._FileTransfer__accept_file('file1', {
            'last_update': 123,
            'deleted': True
        })

        self.assertTrue(self.transfer.transfer_started.notify.called)
        self.assertEqual(self.transfer.file_name, 'file1')
        self.assertEqual(self.transfer.file_data, {
            'last_update': 100
        })
        self.assertEqual(self.transfer.remote_file_data, {
            'last_update': 123,
            'deleted': True
        })

        self.transfer.messanger.send.assert_called_once_with({
            'type': self.transfer.MSG_INIT_ACCEPT
        })

    def test_packet_received_init(self):
        self.transfer._FileTransfer__accept_file = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_INIT,
            'name': 'file1',
            'data': {'test': 'test'}
        })

        self.transfer._FileTransfer__accept_file.assert_called_once_with(
            'file1',
            {'test': 'test'}
        )

    def test_packet_received_cancel(self):
        self.transfer.transfer_cancelled = Mock()
        self.transfer.terminate = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_CANCEL
        })

        self.assertTrue(self.transfer.transfer_cancelled.notify.called)
        self.assertTrue(self.transfer.terminate.called)

    def test_packet_received_block_data(self):
        self.transfer._FileTransfer__data_received = Mock()
        self.transfer._FileTransfer__transfer_started = True

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_BLOCK_DATA,
            'binary_data': b'1234'
        })

        self.transfer._FileTransfer__data_received.assert_called_once_with(
            b'1234'
        )

    def test_packet_received_done(self):
        self.transfer._FileTransfer__complete_transfer = Mock()

        self.transfer._FileTransfer__packet_received({
            'type': self.transfer.MSG_DONE
        })

        self.assertTrue(self.transfer._FileTransfer__complete_transfer.called)

    @patch('pyrsync2.patchstream_block')
    def test_data_received_handler(self, patchstream_block):
        self.transfer._FileTransfer__file_handle = Mock()
        self.transfer._FileTransfer__temp_file_handle = Mock()
        self.transfer.block_size = 128

        self.transfer._FileTransfer__data_received(b'1234')

        patchstream_block.assert_called_once_with(
            self.transfer._FileTransfer__file_handle,
            self.transfer._FileTransfer__temp_file_handle,
            b'1234',
            blocksize=self.transfer.block_size
        )

    @patch('pyrsync2.patchstream_block')
    def test_data_received_handler_error(self, patchstream_block):
        patchstream_block.side_effect = Exception()
        self.transfer.shutdown = Mock()

        self.transfer._FileTransfer__data_received(b'1234')

        self.assertTrue(self.transfer.shutdown.called)

    @patch('syncall.transfers.datetime')
    def test_complete_transfer(self, datetime):
        datetime.now.return_value = Mock()
        datetime.now.return_value.timestamp.return_value = 1234
        self.transfer.remote_file_data = dict()

        file_handle = self.transfer._FileTransfer__file_handle = Mock()
        temp_handle = self.transfer._FileTransfer__temp_file_handle = Mock()

        self.transfer.transfer_completed = Mock()

        self.transfer._FileTransfer__complete_transfer()

        self.assertEqual(self.transfer.timestamp, 1234)
        self.assertTrue(file_handle.close.called)
        self.assertTrue(temp_handle.close.called)
        self.assertTrue(self.transfer.transfer_completed.notify.called)

        self.assertIsNone(self.transfer._FileTransfer__file_handle)
        self.assertIsNone(self.transfer._FileTransfer__temp_file_handle)

        self.transfer.messanger.send.assert_called_once_with({
            'type': self.transfer.MSG_DONE_ACCEPT,
            'time': self.transfer.timestamp
        })

    def test_disconnect_handler_failed(self):
        self.transfer._FileTransfer__release_resources = Mock()
        self.transfer.transfer_failed = Mock()

        self.transfer._FileTransfer__disconnected(None)

        self.assertTrue(self.transfer._FileTransfer__release_resources.called)
        self.assertTrue(self.transfer.transfer_failed.notify.called)

    def test_disconnect_handler_cancelled(self):
        self.transfer._FileTransfer__release_resources = Mock()
        self.transfer.transfer_failed = Mock()
        self.transfer._FileTransfer__transfer_cancelled = True

        self.transfer._FileTransfer__disconnected(None)

        self.assertTrue(self.transfer._FileTransfer__release_resources.called)
        self.assertFalse(self.transfer.transfer_failed.notify.called)

    def test_disconnect_handler_completed(self):
        self.transfer._FileTransfer__release_resources = Mock()
        self.transfer.transfer_failed = Mock()
        self.transfer._FileTransfer__transfer_completed = True

        self.transfer._FileTransfer__disconnected(None)

        self.assertTrue(self.transfer._FileTransfer__release_resources.called)
        self.assertFalse(self.transfer.transfer_failed.notify.called)
