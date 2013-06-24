import unittest
import msgpack
import uuid

from unittest.mock import Mock, MagicMock, patch

import syncall


class ConnectionListenerTests(unittest.TestCase):

    @patch("socket.socket")
    @patch("syncall.network.Messanger")
    def test_connection_init(self, messanger, socket):
        listener = syncall.ConnectionListener('uuid', 1234)
        listener.connection_establiashed = Mock()

        client_socket = Mock()
        client_socket.recv.side_effect = [
            b'1234',
            b'56789123',
            b'4567'
        ]

        serversock = listener.serversock

        serversock.accept.side_effect = [
            (client_socket, ('192.168.0.1', 2456)),
            Exception("Error")
        ]

        listener.run()

        serversock.bind.assert_called_with(('', 1234))
        self.assertTrue(listener.connection_establiashed.called)

    @patch("logging.Logger")
    @patch("socket.socket")
    @patch("syncall.network.Messanger")
    def test_uuid_transfer_error(self, messanger, socket, _):
        listener = syncall.ConnectionListener('uuid', 1234)
        listener.connection_establiashed = Mock()

        client_socket = Mock()
        client_socket.recv.side_effect = [
            b'1234',
            b''
        ]
        client_socket.shutdown.side_effect = Exception("error")

        serversock = listener.serversock

        serversock.accept.side_effect = [
            (client_socket, ('192.168.0.1', 2456)),
            (client_socket, ('192.168.0.1', 2456)),
            Exception("Error")
        ]

        listener.run()

        serversock.bind.assert_called_with(('', 1234))
        self.assertFalse(listener.connection_establiashed.called)
        self.assertTrue(client_socket.shutdown.called)

        client_socket.recv.side_effect = Exception("error")
        listener.run()


class MessangerTests(unittest.TestCase):

    @patch("logging.Logger")
    def setUp(self, _):
        self.messanger = syncall.Messanger(
            MagicMock(),
            ('127.0.0.1', 1234),
            my_uuid='my_uuid',
            remote_uuid='remote_uuid'
        )
        self.disconnected_calls = []
        self.packet_received_calls = []

        def disconnected_handler(data):
            self.disconnected_calls.append(data)

        def packet_received_handler(data):
            self.packet_received_calls.append(data)

        self.messanger.packet_received += packet_received_handler
        self.messanger.disconnected += disconnected_handler

    def tearDown(self):
        del self.messanger

    def test_packet_received(self):
        packet = {
            'test': ['data', 'here'],
            'test_bool': True,
            'test_int': 1,
        }
        packet_bin = msgpack.packb(packet)

        self.messanger.socket.recv.side_effect = [
            packet_bin[:5],
            packet_bin[5:10],
            packet_bin[10:] + packet_bin[:5],
            Exception("test")
        ]

        self.messanger.start_receiving()
        self.messanger.join()

        self.assertEqual(self.disconnected_calls, [None])
        self.assertEqual(self.packet_received_calls, [
            packet
        ])

    def test_decode_error(self):
        packet = {
            'test': [b'decode error here \xffff', 'here'],
            'test_bool': True,
            'test_int': 1,
        }
        packet_bin = msgpack.packb(packet)

        self.messanger.socket.recv.side_effect = [
            packet_bin[:5],
            packet_bin[5:10],
            packet_bin[10:] + packet_bin[:5],
            b''
        ]

        self.messanger.start_receiving()
        self.messanger.join()

        self.assertEqual(self.disconnected_calls, [None])
        self.assertEqual(self.packet_received_calls, [])

    def test_packet_process_error(self):
        packet = {
            'test': ['data', 'here'],
            'test_bool': True,
            'test_int': 1,
        }
        packet_bin = msgpack.packb(packet)

        self.messanger.socket.recv.side_effect = [
            packet_bin[:5],
            packet_bin[5:10],
            packet_bin[10:] + packet_bin[:5],
            Exception("test")
        ]
        mock_handler = Mock()
        mock_handler.side_effect = Exception('test')
        self.messanger.packet_received += mock_handler

        self.messanger.start_receiving()
        self.messanger.join()

        self.assertEqual(self.disconnected_calls, [None])

    @patch("socket.socket")
    def test_connect(self, _):
        my_uuid = str(uuid.uuid1())
        remote_uuid = str(uuid.uuid1())
        msg = syncall.Messanger.connect(
            ('127.0.0.1', 1234),
            my_uuid,
            remote_uuid
        )
        msg.socket.connect.assert_called_with(('127.0.0.1', 1234))
        msg.socket.sendall.assert_called_with(uuid.UUID(my_uuid).bytes)

        self.assertEqual(msg.my_uuid, my_uuid)
        self.assertEqual(msg.remote_uuid, remote_uuid)

    def test_send(self):
        packet = {
            'test': ['data', 'here'],
            'test_bool': True,
            'test_int': 1,
        }

        self.messanger.send(packet)

        self.messanger.socket.send.assert_called_with(
            msgpack.packb(packet)
        )

    def test_send_error(self):
        self.messanger.socket.send.side_effect = Exception("test")
        self.messanger.disconnect = Mock()

        self.messanger.send({'test': 'test'})

        self.assertTrue(self.messanger.disconnect.called)
        self.assertTrue(self.messanger.logger.error.called)

    def test_disconnect(self):
        self.messanger.socket.shutdown = Mock()

        self.messanger.disconnect()
        self.assertTrue(self.messanger.socket.shutdown.called)

        self.messanger.socket.shutdown.side_effect = Exception("test")
        # No exception should be thrown
        self.messanger.disconnect()
