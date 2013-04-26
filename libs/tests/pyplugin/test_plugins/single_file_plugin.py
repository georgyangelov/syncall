from pyplugin import Plugin


class SingleFilePlugin(Plugin):
    def __init__(self):
        super().__init__('SingleFilePlugin', 1)

    def plugin_init(self):
        self.event_manager.notify('single_file_plugin_init')

    def plugin_exit(self):
        self.event_manager.notify('single_file_plugin_exit')
