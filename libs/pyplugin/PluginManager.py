import pkgutil
import inspect
import imp

from . import Plugin


class NoPluginEntryPointError(Exception):
    pass


class PluginManager:
    def __init__(self, plugin_dirs):
        self.plugin_dirs = plugin_dirs
        self.plugins = dict()

    @staticmethod
    def _find_plugin(module):
        for klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, Plugin):
                return klass

        raise NoPluginEntryPointError(
            "Can't find a subclass of pyplugin.Plugin in module '{}'"
            .format(module.__name__)
        )

    def load_all(self):
        for importer, name, _ in pkgutil.walk_packages(self.plugin_dirs):
            module = importer.find_loader(name)[0].load_module()

            plugin_class = PluginManager._find_plugin(module)

            plugin = plugin_class()
            plugin.plugin_init()

            self.plugins[name] = (module, plugin)

    def reload(self, name):
        self.plugins[name][1].plugin_exit()
        imp.reload(self.plugins[name][0])
        self.plugins[name][1].plugin_init()

    def __getitem__(self, name):
        return self.plugins[name][1]
