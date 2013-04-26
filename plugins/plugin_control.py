import logging
import re

from pyplugin.Plugin import *


class TestPlugin(Plugin):
    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)

    @event_handler('app_cmd')
    def handle_cmd(self, data):
        if re.match('reload', data['cmd']):
            match = re.match(r'^reload ([^\s]+)$', data['cmd'])

            if match:
                if match.group(1) in self.plugin_manager.get_plugins():
                    self.plugin_manager.reload(match.group(1))
                else:
                    self.logger.error("No plugin `{}` loaded"
                                      .format(match.group(1)))
            else:
                self.logger.error("Usage: reload <plugin_name>")

            return False
