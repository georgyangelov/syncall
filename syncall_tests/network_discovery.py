import unittest
import msgpack
from unittest.mock import Mock, patch
from events import Event

import syncall
from syncall.network_discovery import BroadcastEventNotifierHandler


class NetworkDiscoveryTests(unittest.TestCase):

    @patch('logging.Logger')
    @patch('syncall.network_discovery.BroadcastListener')
    @patch('socket.socket')
    def setUp(self, socket, BroadcastListener, Logger):
        self.net = syncall.NetworkDiscovery(1234, 2, 'uuid')

    def test_discovery_event(self):
        calls = []

        def handler(data):
            calls.append(data)

        self.net.client_discovered += handler

        self.net._NetworkDiscovery__receive_packet({
            'server': self,
            'source': '127.0.0.1',
            'data': {
                'version': 2,
                'uuid': 'uuid1'
            }
        })

        self.assertEqual(calls, [
            {
                'source': '127.0.0.1',
                'data': {
                    'version': 2,
                    'uuid': 'uuid1'
                }
            }
        ])

    def test_start_listening(self):
        self.net.start_listening()

        self.assertTrue(self.net.listener.start.called)

    def test_shutdown(self):
        self.net.shutdown()

        self.assertTrue(self.net.socket.shutdown.called)

    def test_request(self):
        self.net.request()

        self.net.socket.sendto.assert_called_once_with(
            msgpack.packb({
                'version': 2,
                'uuid': 'uuid'
            }),
            (syncall.network_discovery.BROADCAST_ADDRESS, 1234)
        )

    @patch('socket.socket')
    def test_broadcast_notifier(self, socket):
        class DummyServer:
            def __init__(self):
                self.packet_received = Event()

        class Dummy:
            def __init__(self):
                self.logger = Mock()
                self.packet = msgpack.packb({
                    'version': 1,
                    'uuid': 'uuid1'
                })
                self.server = DummyServer()
                self.client_address = ('192.168.0.3', 1234)

        dummy = Dummy()

        calls = []

        def handler(data):
            calls.append(data)

        dummy.server.packet_received += handler

        BroadcastEventNotifierHandler.handle(dummy)

        self.assertEqual(calls, [
            {
                'data': {
                    'version': 1,
                    'uuid': 'uuid1'
                },
                'source': '192.168.0.3',
                'server': dummy.server
            }
        ])

        dummy.server.packet_received_error = Mock()
        dummy.server.packet_received = Mock()
        dummy.server.packet_received.notify.side_effect = Exception()

        BroadcastEventNotifierHandler.handle(dummy)

        dummy.server.packet_received_error = Mock()
        dummy.packet = dummy.packet[:-4]

        BroadcastEventNotifierHandler.handle(dummy)

        self.assertTrue(dummy.server.packet_received_error.notify.called)

    @patch('syncall.network_discovery.UDPServer')
    @patch('syncall.network_discovery.Thread')
    def test_listener(self, Thread, UDPServer):
        listener = syncall.network_discovery.BroadcastListener(1234)

        self.assertIsInstance(listener.packet_received, Event)
        self.assertIsInstance(listener.packet_received_error, Event)

        listener.serve_forever = Mock()

        listener.run()

        self.assertTrue(listener.serve_forever.called)
