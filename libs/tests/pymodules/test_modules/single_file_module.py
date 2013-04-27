from pymodules.Module import *


class SingleFileModule(Module):
    def __init__(self):
        super().__init__()

    def module_init(self):
        self.event_manager.notify('single_file_module_init')

    def module_exit(self):
        self.event_manager.notify('single_file_module_exit')

    @event_handler('test_event')
    def test_event(self, event_data):
        event_data['tested'] = True

    @data_filter('test_filter')
    def test_filter(self, data):
        data['tested_filter'] = True
