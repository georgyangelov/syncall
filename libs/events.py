class Event:
    def __init__(self, proxy_for=None):
        self.handlers = set()

        if proxy_for is not None:
            proxy_for += notify

    def __iadd__(self, callable):
        self.handlers.add(callable)

        return self

    def __isub__(self, callable):
        self.handlers.remove(callable)

        return self

    def notify(self, data):
        for handler in self.handlers:
            handler(data)

    def __call__(self, data):
        return self.notify(data)
