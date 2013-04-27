import logging
import re

from pymodules.Module import *


class ModuleControl(Module):
    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)

    @event_handler('app_cmd')
    def handle_cmd(self, data):
        if re.match('module', data['cmd']):
            if re.match('module reload', data['cmd']):
                match = re.match(r'^module reload ([^\s]+)$', data['cmd'])

                if match:
                    if match.group(1) == 'all':
                        for module in self.module_manager.get_modules().keys():
                            self.module_manager.reload(module)
                    elif match.group(1) in self.module_manager.get_modules():
                        self.module_manager.reload(match.group(1))
                    else:
                        self.logger.console("No module `{}` loaded"
                                            .format(match.group(1)))
                else:
                    self.logger.console(
                        "Usage: module reload (<module_name>|all)"
                    )

            elif re.match('module list$', data['cmd']):
                self.logger.console(
                    ' '.join(self.module_manager.get_modules().keys())
                )
            else:
                self.logger.console("Usage: module [reload|list]")

            return False  # Stop event propagation
