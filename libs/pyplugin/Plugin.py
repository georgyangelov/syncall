class Plugin:
    def __init__(self, name, version, event_manager, filter_manager):
        self.name = name
        self.version = version
        self.event_manager = event_manager
        self.filter_manager = filter_manager

    def plugin_init(self):
        pass

    def plugin_exit(self):
        pass
