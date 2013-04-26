import pkgutil
import inspect
import imp

from pyplugin import Plugin, EventManager, DataFilterManager


class NoPluginEntryPointError(Exception):
    pass


class PluginManager:
    def __init__(self, plugin_dirs):
        self.plugin_dirs = plugin_dirs
        self.plugins = dict()
        self.event_manager = EventManager()
        self.filter_manager = DataFilterManager()

    @staticmethod
    def _find_plugin(module):
        for _, klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, Plugin) and klass is not Plugin:
                return klass

        raise NoPluginEntryPointError(
            "Can't find a subclass of pyplugin.Plugin in module '{}'"
            .format(module.__name__)
        )

    def set_up_plugin(self, plugin_class):
        plugin = plugin_class()
        plugin.event_manager = self.event_manager
        plugin.filter_manager = self.filter_manager
        plugin.plugin_init()

        return plugin

    def load_all(self):
        for importer, name, _ in pkgutil.walk_packages(self.plugin_dirs):
            module = importer.find_loader(name)[0].load_module()

            plugin_class = PluginManager._find_plugin(module)

            self.plugins[name] = (module, self.set_up_plugin(plugin_class))

    def reload(self, name):
        self.plugins[name][1].plugin_exit()

        module = imp.reload(self.plugins[name][0])
        plugin_class = PluginManager._find_plugin(module)

        self.plugins[name] = (module, self.set_up_plugin(plugin_class))

    def __getitem__(self, name):
        return self.plugins[name][1]
