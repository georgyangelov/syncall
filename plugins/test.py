from pyplugin import Plugin


class TestPlugin(Plugin):
    def plugin_init(self):
        self.event_manager.notify('single_file_plugin_init')

    def plugin_exit(self):
        self.event_manager.notify('single_file_plugin_exit')
