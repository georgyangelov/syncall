import logging
import re

from pymodules.Module import *


class TestModule(Module):
    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)

    @event_handler('app_cmd')
    def handle_cmd(self, data):
        if re.match('reload', data['cmd']):
            match = re.match(r'^reload ([^\s]+)$', data['cmd'])

            if match:
                if match.group(1) in self.module_manager.get_modules():
                    self.module_manager.reload(match.group(1))
                else:
                    self.logger.error("No module `{}` loaded"
                                      .format(match.group(1)))
            else:
                self.logger.error("Usage: reload <module_name>")

            return False
