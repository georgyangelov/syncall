import unittest
import os

from pyplugin.PluginManager import *
from pyplugin.EventManager import *
from pyplugin.DataFilterManager import *

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class PluginManagerTests(unittest.TestCase):

    def get_plugin_manager(self):
        return PluginManager([CURRENT_DIR + '/test_plugins'])

    def test_single_file_plugin(self):
        manager = self.get_plugin_manager()

        loaded = 0
        exited = 0

        def load_handler(event):
            nonlocal loaded
            loaded += 1

        def exit_handler(event):
            nonlocal exited
            exited += 1

        manager.event_manager.on('single_file_plugin_init', load_handler)
        manager.event_manager.on('single_file_plugin_exit', exit_handler)
        manager.load_all()

        self.assertEqual(manager.get_plugins().keys(), {
            'single_file_plugin'
        })

        self.assertEqual(loaded, 1)
        self.assertEqual(exited, 0)

        manager.reload('single_file_plugin')

        self.assertEqual(exited, 1)
        self.assertEqual(loaded, 2)
