import unittest
from time import sleep

from decorator_utils import delay, delay_keys


class DecoratorUtilsTests(unittest.TestCase):

    def test_delay(self):
        calls = []

        @delay(0.01)
        def dummy_func():
            calls.append('called')

        dummy_func()
        self.assertEqual(len(calls), 0)
        sleep(0.03)
        self.assertEqual(calls, ['called'])

    def test_no_delay(self):
        calls = []

        @delay(0)
        def dummy_func():
            calls.append('called')

        dummy_func()
        self.assertEqual(calls, ['called'])

    def test_delay_keys(self):
        calls = []

        @delay_keys(0.01, lambda string: string)
        def dummy_func(string):
            calls.append(string)

        dummy_func('test')
        dummy_func('test2')
        dummy_func('test')
        dummy_func('test2')
        dummy_func('test')

        sleep(0.03)

        self.assertEqual(set(calls), {'test', 'test2'})
