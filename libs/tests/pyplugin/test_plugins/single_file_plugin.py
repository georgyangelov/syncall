from pyplugin.Plugin import *


class SingleFilePlugin(Plugin):
    def __init__(self):
        super().__init__('SingleFilePlugin', 1)

    def plugin_init(self):
        self.event_manager.notify('single_file_plugin_init')

    def plugin_exit(self):
        self.event_manager.notify('single_file_plugin_exit')

    @event_handler('test_event')
    def test_event(self, event_data):
        event_data['tested'] = True

    @data_filter('test_filter')
    def test_filter(self, data):
        data['tested_filter'] = True
