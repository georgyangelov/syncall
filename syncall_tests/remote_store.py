import unittest

from unittest.mock import Mock, MagicMock, patch

import syncall


class RemoteStoreTests(unittest.TestCase):

    @patch("logging.Logger")
    def setUp(self, logger):
        self.remote = syncall.RemoteStore(
            MagicMock(),
            Mock()
        )
        self.remote.directory.diff = MagicMock()

    def tearDown(self):
        del self.remote

    def test_index_received(self):
        self.assertFalse(self.remote.index_received())

        self.remote.remote_index = {
            'file1': {
                'test': 'test'
            }
        }

        self.assertTrue(self.remote.index_received())

    def test_request_transfer(self):
        transfer_messanger = Mock()

        self.remote.request_transfer(transfer_messanger)

        manager = self.remote.directory.transfer_manager
        manager.process_transfer.assert_called_with(
            self.remote,
            transfer_messanger
        )

    def test_start_receiving(self):
        self.remote.directory.get_last_update.return_value = 5
        self.remote.directory.get_index.return_value = {
            'index': 'test'
        }

        self.remote.start_receiving()

        self.assertTrue(self.remote.messanger.start_receiving.called)
        self.remote.messanger.send.assert_called_once_with({
            'type': syncall.remote_store.MSG_INDEX,
            'index': {
                'index': 'test'
            }
        })

    def test_send_index(self):
        self.remote.my_index_last_updated = 5
        self.remote.directory.get_last_update.return_value = 5
        self.remote.directory.get_index.return_value = {
            'index': 'test'
        }

        self.remote.send_index()
        self.remote.messanger.send.assert_called_once_with({
            'type': syncall.remote_store.MSG_INDEX_NO_CHANGE
        })

        self.remote.directory.get_last_update.return_value = 6

        self.remote.send_index(request=True)
        self.remote.messanger.send.assert_any_call({
            'type': syncall.remote_store.MSG_INDEX,
            'index': {
                'index': 'test'
            }
        })
        self.remote.messanger.send.assert_any_call({
            'type': syncall.remote_store.MSG_REQUEST_INDEX
        })

    def test_send_index_delta(self):
        self.remote.directory.get_last_update.return_value = 5
        self.remote.directory.get_index.return_value = {
            'file1': {'test1': 'test1'},
            'file2': {'test2': 'test2'}
        }

        self.remote.send_index_delta(
            {
                'file1',
                'file2'
            },
            request=False
        )

        self.assertEqual(self.remote.my_index_last_updated, 5)
        self.remote.messanger.send.assert_called_once_with({
            'type': syncall.remote_store.MSG_INDEX_DELTA,
            'index': {
                'file1': {'test1': 'test1'},
                'file2': {'test2': 'test2'}
            }
        })

        self.remote.send_index_delta(
            {
                'file1',
                'file2'
            },
            request=True
        )

        self.remote.messanger.send.assert_any_call({
            'type': syncall.remote_store.MSG_REQUEST_INDEX
        })

    def test_disconnect_handler(self):
        handler = Mock()
        self.remote.disconnected += handler

        self.remote._RemoteStore__disconnected(None)

        manager = self.remote.directory.transfer_manager
        manager.remote_disconnect.assert_called_once_with(self.remote)
        handler.assert_called_once_with(self.remote)

    def test_disconnect(self):
        self.remote.disconnect()

        self.remote.messanger.disconnect.assert_called_once_with()

    def test_packet_index(self):
        directory = self.remote.directory
        packet = {
            'type': syncall.remote_store.MSG_INDEX,
            'index': {
                'file1': {
                    'test': 'test'
                }
            }
        }
        directory.diff.return_value = (
            {'file1'},
            set(),
            set()
        )

        self.remote._packet_received(packet)

        directory.transfer_manager.sync_files.assert_called_once_with(
            self.remote,
            {'file1'}
        )
        self.assertEqual(self.remote.remote_index, packet['index'])

    def test_no_type_ignore(self):
        self.remote._packet_received({
            'test': 'test'
        })

    def test_invalid_type_ignore(self):
        self.remote._packet_received({
            'type': 99999
        })

    def test_packet_index_delta(self):
        index_delta = {
            'file1': {
                'test1': 'test1'
            },
            'file2': {
                'test2': 'test2'
            }
        }
        self.remote.remote_index = {
            'file1': {
                'test3': 1234
            },
            'file3': {
                'test4': 54321
            }
        }

        self.remote._packet_received({
            'type': syncall.remote_store.MSG_INDEX_DELTA,
            'index': index_delta
        })

        self.assertEqual(self.remote.remote_index, {
            'file1': {
                'test1': 'test1'
            },
            'file2': {
                'test2': 'test2'
            },
            'file3': {
                'test4': 54321
            }
        })
        self.remote.directory.diff.assert_called_once_with(
            self.remote.remote_index
        )

    def test_packet_request_index(self):
        self.remote.send_index = Mock()

        self.remote._packet_received({
            'type': syncall.remote_store.MSG_REQUEST_INDEX
        })

        self.remote.send_index.assert_called_once_with(request=False)

    def test_packet_index_no_change(self):
        self.remote._RemoteStore__remote_index_updated = Mock()

        self.remote._packet_received({
            'type': syncall.remote_store.MSG_INDEX_NO_CHANGE
        })

        self.assertTrue(self.remote._RemoteStore__remote_index_updated.called)
