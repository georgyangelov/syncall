class EventManager:
    """Dispatches events and notifies event handlers."""

    def __init__(self):
        self.handlers = dict()

    def on(self, event_name, handler, priority=1):
        handler_list = self.handlers.setdefault(event_name, [])

        self.off(event_name, handler)

        handler_list.append((handler, priority))
        handler_list.sort(key=lambda x: x[1], reverse=True)

    def off(self, event_name, handler):
        handler_func_list = [handler for (handler, priority)
                             in self.handlers[event_name]]

        if handler in handler_func_list:
            del self.handlers[event_name][handler_func_list.index(handler)]

    def notify(self, event_name, event_data=None):
        if event_name not in self.handlers:
            return True

        for (handler, _) in self.handlers[event_name]:
            try:
                success = handler(event_data)

                if success is False:  # None == True
                    return False
            except StopPropagation:
                break

        return True


class StopPropagation(Exception):
    pass
