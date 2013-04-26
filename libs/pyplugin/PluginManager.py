import pkgutil
import inspect
import imp

from pyplugin import Plugin, EventManager, DataFilterManager


class NoPluginEntryPointError(Exception):
    pass


class PluginManager:
    def __init__(self, plugin_dirs):
        self.plugin_dirs = plugin_dirs
        self._plugins = dict()
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

    def set_up_plugin(self, name, plugin_class):
        plugin = plugin_class()
        plugin.event_manager = self.event_manager
        plugin.filter_manager = self.filter_manager

        if plugin.name is None:
            plugin.name = name

        plugin.plugin_init()

        return plugin

    def load_all(self):
        for importer, name, _ in pkgutil.walk_packages(self.plugin_dirs):
            module = importer.find_loader(name)[0].load_module()

            plugin_class = PluginManager._find_plugin(module)
            plugin_object = self.set_up_plugin(name, plugin_class)

            self._plugins[name] = (module, plugin_object)

    def reload(self, name):
        self._plugins[name][1].plugin_exit()

        module = imp.reload(self._plugins[name][0])
        plugin_class = PluginManager._find_plugin(module)

        self._plugins[name] = (module, self.set_up_plugin(name, plugin_class))

    def get_plugins(self):
        return {name: plugin[1] for name, plugin in self._plugins.items()}

    def __getitem__(self, name):
        return self._plugins[name][1]
