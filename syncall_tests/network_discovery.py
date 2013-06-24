import unittest
import msgpack
from unittest.mock import Mock, patch
from events import Event

import syncall
from syncall.network_discovery import BroadcastEventNotifierHandler


class NetworkDiscoveryTests(unittest.TestCase):

    @patch('socket.socket')
    def test_discovery_event(self, socket):
        net = syncall.NetworkDiscovery(1234, 2, 'uuid')

        calls = []

        def handler(data):
            calls.append(data)

        net.client_discovered += handler

        net._NetworkDiscovery__receive_packet({
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

    @patch('socket.socket')
    def test_request(self, socket):
        net = syncall.NetworkDiscovery(1234, 2, 'uuid')

        calls = []

        def broadcast(data, port):
            calls.append((data, port))

        net._NetworkDiscovery__broadcast = broadcast

        net.request()

        self.assertEqual(calls, [
            (
                {
                    'version': 2,
                    'uuid': 'uuid'
                },
                1234
            )
        ])

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
