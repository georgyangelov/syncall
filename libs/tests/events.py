import unittest

import events


class EventTests(unittest.TestCase):
    def test_event_no_data(self):
        calls = []

        def handler(data):
            calls.append(data)

        event = events.Event()
        event += handler

        event.notify()
        event()

        self.assertEqual(calls, [None, None])

    def test_proxy_event(self):
        calls = []

        def handler(data):
            calls.append(data)

        event = events.Event()
        proxy = events.Event(proxy_for=event)

        proxy += handler

        event.notify('test')

        self.assertEqual(calls, ['test'])

    def test_event_with_data(self):
        calls = []

        def handler(data):
            calls.append(data)

        event = events.Event()
        event += handler

        data = {
            "test": "string",
            "test2": 1234
        }

        event.notify(data)
        event.notify(data)

        self.assertEqual(calls, [data, data])

    def test_multiple_handlers(self):
        calls = set()

        def handler_one(data):
            calls.add("one")

        def handler_two(data):
            calls.add("two")

        event = events.Event()
        event += handler_one
        event += handler_two

        event.notify()

        self.assertEqual(calls, {"one", "two"})

    def test_remove_handler(self):
        calls = set()

        def handler_one(data):
            calls.add("one")

        def handler_two(data):
            calls.add("two")

        event = events.Event()
        event += handler_one
        event += handler_two

        event -= handler_one

        event.notify()

        self.assertEqual(calls, {'two'})

    def test_clear_handlers(self):
        calls = set()

        def handler_one(data):
            calls.add("one")

        def handler_two(data):
            calls.add("two")

        event = events.Event()
        event += handler_one
        event += handler_two

        event.clear_handlers()

        self.assertEqual(calls, set())
