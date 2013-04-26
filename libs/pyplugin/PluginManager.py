import pkgutil
import inspect
import imp
import logging

from pyplugin import Plugin, EventManager, DataFilterManager


class NoPluginEntryPointError(Exception):
    pass


class PluginManager:
    def __init__(self, plugin_dirs):
        self.plugin_dirs = plugin_dirs
        self._plugins = dict()
        self.plugin_manager = self
        self.event_manager = EventManager()
        self.filter_manager = DataFilterManager()
        self.logger = logging.getLogger(__name__)

    def _find_plugin(self, module):
        for class_name, klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, Plugin) and klass is not Plugin:
                self.logger.debug('Found `{}` class as entry point for `{}`'
                                  .format(class_name, module.__name__))
                return klass

        raise NoPluginEntryPointError(
            "Can't find a subclass of pyplugin.Plugin in module '{}'"
            .format(module.__name__)
        )

    def set_up_plugin(self, name, plugin_class):
        self.logger.debug('Initializing plugin `{}`'.format(name))

        plugin = plugin_class()
        plugin.event_manager = self.event_manager
        plugin.filter_manager = self.filter_manager

        if plugin.name is None:
            plugin.name = name

        plugin.plugin_init()
        plugin._attach_handlers()
        self.logger.info('Initialized plugin `{}`'.format(name))

        return plugin

    def load_all(self):
        for importer, name, _ in pkgutil.walk_packages(self.plugin_dirs):
            self.logger.info('Loading plugin `{}`'.format(name))

            module = importer.find_loader(name)[0].load_module()

            plugin_class = self._find_plugin(module)
            plugin_object = self.set_up_plugin(name, plugin_class)

            self._plugins[name] = (module, plugin_object)

    def reload(self, name):
        self.logger.debug('Reloading plugin `{}`'.format(name))
        self._plugins[name][1].plugin_exit()
        self._plugins[name][1]._detach_handlers()

        module = imp.reload(self._plugins[name][0])
        plugin_class = self._find_plugin(module)

        self._plugins[name] = (module, self.set_up_plugin(name, plugin_class))
        self.logger.info('Plugin `{}` reloaded'.format(name))

    def get_plugins(self):
        return {name: plugin[1] for name, plugin in self._plugins.items()}

    def __getitem__(self, name):
        return self._plugins[name][1]
