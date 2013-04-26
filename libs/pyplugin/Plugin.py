import inspect


class Plugin:
    def __init__(self, name=None, version=1):
        self.name = name
        self.version = version

    def plugin_init(self):
        pass

    def plugin_exit(self):
        pass

    def _attach_handlers(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)

        for method_name, method in methods:
            if hasattr(method, '_attach'):
                method._attach(self)

    def _detach_handlers(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)

        for method_name, method in methods:
            if hasattr(method, '_detach'):
                method._detach(self)


def event_handler(event_name, priority=1):
    def wrapper(func):
        def attach(plugin):
            bound_func = func.__get__(plugin, plugin.__class__)
            plugin.event_manager.on(event_name, bound_func, priority)

        def detach(plugin):
            bound_func = func.__get__(plugin, plugin.__class__)
            plugin.event_manager.off(event_name, bound_func)

        func._event_name = event_name
        func._event_priority = priority
        func._attach = attach
        func._detach = detach

        return func

    return wrapper


def data_filter(channel, priority=1):
    def wrapper(func):
        def attach(plugin):
            bound_func = func.__get__(plugin, plugin.__class__)
            plugin.filter_manager.on(channel, bound_func, priority)

        def detach(plugin):
            bound_func = func.__get__(plugin, plugin.__class__)
            plugin.filter_manager.off(channel, bound_func)

        func._filter_name = channel
        func._filter_priority = priority
        func._attach = attach
        func._detach = detach

        return func

    return wrapper
