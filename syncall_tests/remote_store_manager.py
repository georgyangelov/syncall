from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

import syncall


class RemoteStoreManagerTests(TestCase):

    @patch('logging.Logger')
    def setUp(self, Logger):
        self.manager = syncall.RemoteStoreManager(
            network_discovery=MagicMock(),
            connection_listener=MagicMock(),
            transfer_listener=MagicMock(),
            directory=MagicMock(),
            id='uuid'
        )

        self.remotes = [
            Mock(), Mock(), Mock()
        ]

        for uuid, remote in enumerate(self.remotes):
            self.manager.remotes['uuid' + str(uuid)] = remote

    def tearDown(self):
        del self.manager

    def test_shutdown(self):
        self.manager.shutdown()

        for remote in self.remotes:
            self.assertTrue(remote.disconnect.called)

    def test_send_whole_index(self):
        self.manager.send_index()

        for remote in self.remotes:
            self.assertTrue(remote.send_index.called)

    def test_send_index_delta(self):
        self.manager.send_index({'file1', 'file2', 'file3'})

        for remote in self.remotes:
            remote.send_index_delta.assert_called_once_with({
                'file1', 'file2', 'file3'
            })

    def test_index_update_handler(self):
        delta = {'file1', 'file2', 'file3'}
        self.manager.send_index = Mock()

        self.manager._RemoteStoreManager__index_updated(delta)

        self.manager.send_index.assert_called_once_with(delta)

    def test_index_no_update(self):
        delta = set()
        self.manager.send_index = Mock()

        self.manager._RemoteStoreManager__index_updated(delta)

        self.assertFalse(self.manager.send_index.called)

    def test_transfer_started_handler_invalid(self):
        messanger = MagicMock()
        messanger.remote_uuid = 'non_connected_uuid'

        self.manager._RemoteStoreManager__transfer_initiated(messanger)

        self.assertTrue(messanger.disconnect.called)
        for remote in self.remotes:
            self.assertFalse(remote.request_transfer.called)

    def test_trasnfer_started_handler(self):
        messanger = MagicMock()
        messanger.remote_uuid = 'uuid1'

        self.manager._RemoteStoreManager__transfer_initiated(messanger)

        self.assertFalse(messanger.disconnect.called)
        self.remotes[1].request_transfer.assert_called_once_with(messanger)

    @patch('syncall.RemoteStore')
    def test_client_connected_handler(self, RemoteStore):
        messanger = MagicMock()
        messanger.remote_uuid = 'uuid2'

        self.manager._RemoteStoreManager__client_connected(messanger)

        self.assertTrue(self.remotes[2].disconnect.called)
        RemoteStore.assert_called_once_with(messanger, self.manager.directory)
        self.assertTrue(self.manager.remotes['uuid2'].start_receiving.called)

    @patch('syncall.Messanger.connect')
    @patch('syncall.RemoteStore')
    def test_client_discovered_handler(self, RemoteStore, MessangerConnect):
        data = {
            'source': '127.0.0.1',
            'data': {
                'uuid': 'remote_uuid'
            }
        }

        self.manager._RemoteStoreManager__client_discovered(data)

        MessangerConnect.assert_called_once_with(
            ('127.0.0.1', syncall.DEFAULT_PORT),
            self.manager.uuid,
            'remote_uuid'
        )
        self.assertIn('remote_uuid', self.manager.remotes)

    @patch('syncall.Messanger.connect')
    @patch('syncall.RemoteStore')
    def test_client_discovered_error(self, RemoteStore, MessangerConnect):
        data = {
            'source': '127.0.0.1',
            'data': {
                'uuid': 'remote_uuid'
            }
        }
        MessangerConnect.side_effect = Exception()

        self.manager._RemoteStoreManager__client_discovered(data)

        self.assertNotIn('remote_uuid', self.manager.remotes)
        self.assertFalse(RemoteStore.called)

    def test_client_disconnected_handler(self):
        self.manager.remotes['uuid2'].uuid = 'uuid2'

        self.manager._RemoteStoreManager__client_disconnected(
            self.manager.remotes['uuid2']
        )

        self.assertNotIn('uuid2', self.manager.remotes)
