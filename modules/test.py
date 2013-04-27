from pymodules import Module


class TestModule(Module):
    def module_init(self):
        self.event_manager.notify('single_file_module_init')

    def module_exit(self):
        self.event_manager.notify('single_file_module_exit')
