class Event:
    def __init__(self, proxy_for=None):
        self.handlers = set()

        if proxy_for is not None:
            proxy_for += self.notify

    def __iadd__(self, callable):
        self.handlers.add(callable)

        return self

    def __isub__(self, callable):
        self.handlers.remove(callable)

        return self

    def notify(self, data=None):
        for handler in self.handlers:
            handler(data)

    def clear_handlers(self):
        self.handlers.clear()

    def __call__(self, data=None):
        return self.notify(data)
