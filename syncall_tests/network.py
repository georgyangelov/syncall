import unittest

from unittest.mock import Mock, patch

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
