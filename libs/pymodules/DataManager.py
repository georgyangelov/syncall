import logging


class DataManager:
    """Maps data through a series of data provider functions."""

    def __init__(self):
        self.providers = dict()
        self.logger = logging.getLogger(__name__)

    def on(self, channel, data_provider, priority=1):
        handler_list = self.providers.setdefault(channel, [])

        handler_list.append((data_provider, priority))
        handler_list.sort(key=lambda x: x[1], reverse=True)

        self.logger.debug('Attached data provider for `{}` ({})'
                          .format(channel, priority))

    def off(self, channel, data_provider):
        handler_func_list = [data_provider for (data_provider, priority)
                             in self.providers[channel]]

        if data_provider in handler_func_list:
            del self.providers[channel][handler_func_list.index(data_provider)]
            self.logger.debug('Removed data provider for `{}`'.format(channel))

    def map(self, channel, data=None):
        self.logger.debug(
            'Requesting data for `{}`'.format(channel),
            extra={'data': data}
        )

        if channel not in self.providers:
            self.logger.debug(
                'No data providers for `{}`'.format(channel)
            )

            return data

        for (data_provider, _) in self.providers[channel]:
            try:
                data_provider(data)
            except StopPropagation:
                self.logger.error('Provider stopped propagation of `{}`'
                                  .format(channel))
                break

        self.logger.debug(
            'Data for `{}` processed'.format(channel),
            extra={'data': data}
        )

        return data

    def request(self, channel):
        return self.map(channel, None)

    def providers_for(self, channel):
        if channel not in self.providers:
            return tuple()

        return tuple(data_provider
                     for (data_provider, _) in self.providers[channel])
