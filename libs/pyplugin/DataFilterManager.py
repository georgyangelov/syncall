class DataFilterManager:
    """Maps data through a series of data filter functions."""

    def __init__(self):
        self.filters = dict()

    def on(self, channel, data_filter, priority=1):
        handler_list = self.filters.setdefault(channel, [])

        handler_list.append((data_filter, priority))
        handler_list.sort(key=lambda x: x[1], reverse=True)

    def off(self, channel, data_filter):
        handler_func_list = [data_filter for (data_filter, priority)
                             in self.filters[channel]]

        if data_filter in handler_func_list:
            del self.filters[channel][handler_func_list.index(data_filter)]

    def map(self, channel, data=None):
        if channel not in self.filters:
            return data

        for (data_filter, _) in self.filters[channel]:
            try:
                data_filter(data)
            except StopPropagation:
                break

        return data

    def request(self, channel):
        return self.map(channel, None)

    def handlers_for(self, channel):
        if channel not in self.filters:
            return tuple()

        return tuple(data_filter for (data_filter, _) in self.filters[channel])
