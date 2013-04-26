class Plugin:
    def __init__(self, name, version):
        self.name = name
        self.version = version

    def plugin_init(self):
        pass

    def plugin_exit(self):
        pass
