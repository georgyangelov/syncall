import unittest

from pymodules.DataFilterManager import *


class DataFilterManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = DataFilterManager()

    def tearDown(self):
        del self.manager

    def test_no_filters(self):
        data = self.manager.map('no_filters', {'data': 1234})
        self.assertEqual(data, {'data': 1234})
        self.assertEqual(self.manager.handlers_for('no_filters'), tuple())

    def test_one_filter(self):
        def filter_one(data):
            data['dummy'] = 1234

        self.manager.on('one_filter', filter_one)

        data = self.manager.map('one_filter', {'dummy': 4444})
        self.assertEqual(data, {'dummy': 1234})
        self.assertEqual(
            self.manager.handlers_for('one_filter'),
            (filter_one,)
        )

    def test_multiple_filters(self):
        def filter_one(data):
            data['dummy'] += 1

        self.manager.on('multiple_filters', filter_one)
        self.manager.on('multiple_filters', filter_one)

        data = self.manager.map('multiple_filters', {'dummy': 0})
        self.assertEqual(data, {'dummy': 2})
        self.assertEqual(
            self.manager.handlers_for('multiple_filters'),
            (filter_one, filter_one)
        )

    def test_priorities(self):
        def dummy_1(data):
            data['list'].append(1)

        def dummy_2(data):
            data['list'].append(2)

        def dummy_3(data):
            data['list'].append(3)

        def dummy_4(data):
            data['list'].append(4)

        def dummy_5(data):
            data['list'].append(5)

        self.manager.on('priorities', dummy_2, 2)
        self.manager.on('priorities', dummy_3, 3)
        self.manager.on('priorities', dummy_5, 5)
        self.manager.on('priorities', dummy_1, 1)
        self.manager.on('priorities', dummy_4, 4)

        data = self.manager.map('priorities', {'list': []})

        self.assertEqual(data, {'list': [5, 4, 3, 2, 1]})
        self.assertEqual(
            self.manager.handlers_for('priorities'),
            (dummy_5, dummy_4, dummy_3, dummy_2, dummy_1)
        )
