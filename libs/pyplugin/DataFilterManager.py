import logging


class DataFilterManager:
    """Maps data through a series of data filter functions."""

    def __init__(self):
        self.filters = dict()
        self.logger = logging.getLogger(__name__)

    def on(self, channel, data_filter, priority=1):
        handler_list = self.filters.setdefault(channel, [])

        handler_list.append((data_filter, priority))
        handler_list.sort(key=lambda x: x[1], reverse=True)

        self.logger.debug('Attached data filter for `{}` ({})'
                          .format(channel, priority))

    def off(self, channel, data_filter):
        handler_func_list = [data_filter for (data_filter, priority)
                             in self.filters[channel]]

        if data_filter in handler_func_list:
            del self.filters[channel][handler_func_list.index(data_filter)]
            self.logger.debug('Removed data filter for `{}`'.format(channel))

    def map(self, channel, data=None):
        self.logger.debug(
            'Requesting data for `{}`'.format(channel),
            extra={'data': data}
        )

        if channel not in self.filters:
            return data

        for (data_filter, _) in self.filters[channel]:
            try:
                data_filter(data)
            except StopPropagation:
                self.logger.error('Filter stopped propagation of `{}`'
                                  .format(channel))
                break

        self.logger.debug(
            'Data for `{}` processed'.format(channel),
            extra={'data': data}
        )

        return data

    def request(self, channel):
        return self.map(channel, None)

    def handlers_for(self, channel):
        if channel not in self.filters:
            return tuple()

        return tuple(data_filter for (data_filter, _) in self.filters[channel])
