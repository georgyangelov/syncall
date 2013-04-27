import pkgutil
import inspect
import imp
import logging

from pymodules import Module, EventManager, DataManager


class NoModuleEntryPointError(Exception):
    pass


class ModuleManager:
    def __init__(self, module_dirs):
        self.module_dirs = module_dirs
        self._modules = dict()
        self.event_manager = EventManager()
        self.data_manager = DataManager()
        self.logger = logging.getLogger(__name__)

    def _find_module(self, module):
        for class_name, klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, Module) and klass is not Module:
                self.logger.debug('Found `{}` class as entry point for `{}`'
                                  .format(class_name, module.__name__))
                return klass

        raise NoModuleEntryPointError(
            "Can't find a subclass of pymodules.Module in module '{}'"
            .format(module.__name__)
        )

    def set_up_module(self, name, module_class):
        self.logger.debug('Initializing module `{}`'.format(name))

        module = module_class()
        module.module_manager = self
        module.event_manager = self.event_manager
        module.data_manager = self.data_manager

        if module.name is None:
            module.name = name

        module._attach_handlers()
        module.module_init()
        self.logger.info('Initialized module `{}`'.format(name))

        return module

    def load_all(self, reload=False):
        for importer, name, _ in pkgutil.walk_packages(self.module_dirs):
            if name in self._modules:
                if reload:
                    self.reload(name)
                continue

            self.logger.info('Loading module `{}`'.format(name))

            module = importer.find_loader(name)[0].load_module()

            module_class = self._find_module(module)
            module_object = self.set_up_module(name, module_class)

            self._modules[name] = (module, module_object)

            self.event_manager.notify('module_load', {
                'name': name,
                'module': module_object,
                'python_module': module
            })

    def reload(self, name):
        self.logger.debug('Reloading module `{}`'.format(name))
        self._modules[name][1].module_exit()
        self._modules[name][1]._detach_handlers()

        module = imp.reload(self._modules[name][0])
        module_class = self._find_module(module)

        self._modules[name] = (module, self.set_up_module(name, module_class))
        self.logger.info('Module `{}` reloaded'.format(name))

        self.event_manager.notify('module_reload', {
            'name': name,
            'module': self._modules[name],
            'python_module': module
        })

    def unload(self, name):
        self.logger.debug('Unloading module `{}`'.format(name))
        self._modules[name][1].module_exit()
        self._modules[name][1]._detach_handlers()

        del self._modules[name]
        self.logger.debug('Unloaded module `{}`'.format(name))

        self.event_manager.notify('module_unload', {
            'name': name
        })

    def get_modules(self):
        return {name: module[1] for name, module in self._modules.items()}

    def _all_modules(self):
        return self._modules

    def __getitem__(self, name):
        return self._modules[name][1]
