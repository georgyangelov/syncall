import unittest

from pyplugin.EventManager import *


class EventManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = EventManager()

    def tearDown(self):
        del self.manager

    def test_no_handlers(self):
        self.assertTrue(self.manager.notify('eventname', dict()))

    def test_single_handler(self):
        x = 0

        def dummy_handler(event):
            nonlocal x
            x += event['num']

        self.manager.on('test_single_handler', dummy_handler)

        self.assertTrue(self.manager.notify('test_single_handler', {'num': 1}))
        self.assertEqual(x, 1)

    def test_multiple_handlers(self):
        x = []

        def dummy_handler_1(event):
            x.append(1)

        def dummy_handler_2(event):
            x.append(2)

        self.manager.on('test_multiple_handlers', dummy_handler_1)
        self.manager.on('test_multiple_handlers', dummy_handler_2)

        self.assertTrue(self.manager.notify('test_multiple_handlers', dict()))
        self.assertEqual(set(x), {1, 2})

    def test_priorities(self):
        x = []

        def dummy_handler_1(event):
            x.append(1)

        def dummy_handler_2(event):
            x.append(2)

        def dummy_handler_3(event):
            x.append(3)

        def dummy_handler_4(event):
            x.append(4)

        def dummy_handler_5(event):
            x.append(5)

        self.manager.on('test_priorities', dummy_handler_3, 1)
        self.manager.on('test_priorities', dummy_handler_4, 0.5)
        self.manager.on('test_priorities', dummy_handler_2, 2)
        self.manager.on('test_priorities', dummy_handler_1, 3)
        self.manager.on('test_priorities', dummy_handler_5, 0)

        self.assertTrue(self.manager.notify('test_priorities', dict()))
        self.assertEqual(x, [1, 2, 3, 4, 5])

    def test_remove_handler(self):
        x = []

        def dummy_handler(event):
            x.append(1)

        def dummy_handler_2(event):
            x.append(2)

        self.manager.on('test_remove_handler', dummy_handler_2)
        self.manager.on('test_remove_handler', dummy_handler)
        self.manager.off('test_remove_handler', dummy_handler_2)

        self.assertTrue(self.manager.notify('test_remove_handler', dict()))
        self.assertEqual(x, [1])
