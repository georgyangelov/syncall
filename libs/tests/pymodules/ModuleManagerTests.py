import unittest
import os

from pymodules.ModuleManager import *
from pymodules.EventManager import *
from pymodules.DataFilterManager import *

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class ModuleManagerTests(unittest.TestCase):

    def get_module_manager(self):
        return ModuleManager([CURRENT_DIR + '/test_modules'])

    def test_single_file_module(self):
        manager = self.get_module_manager()

        loaded = 0
        exited = 0

        def load_handler(event):
            nonlocal loaded
            loaded += 1

        def exit_handler(event):
            nonlocal exited
            exited += 1

        manager.event_manager.on('single_file_module_init', load_handler)
        manager.event_manager.on('single_file_module_exit', exit_handler)
        manager.load_all()

        self.assertEqual(manager.get_modules().keys(), {
            'single_file_module'
        })

        self.assertEqual(loaded, 1)
        self.assertEqual(exited, 0)

        manager.reload('single_file_module')

        self.assertEqual(exited, 1)
        self.assertEqual(loaded, 2)

    def test_event_decorator(self):
        manager = self.get_module_manager()
        manager.load_all()

        data = {'tested': False}

        self.assertTrue(manager.event_manager.notify('test_event', data))
        self.assertTrue(data['tested'])

    def test_filter_decorator(self):
        manager = self.get_module_manager()
        manager.load_all()

        data = {'tested_filter': False}

        self.assertEqual(
            manager.filter_manager.map('test_filter', data),
            {'tested_filter': True}
        )
        self.assertEqual(data, {'tested_filter': True})
