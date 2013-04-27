import logging
import re
import os

import pathext

from pymodules.Module import *


class ModuleControl(Module):
    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)

    def module_init(self):
        self.event_manager.notify('update_monitored_dirs')

    def module_exit(self):
        self.event_manager.notify('update_monitored_dirs')

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

    @data_provider('monitor_dirs')
    def monitor_dirs(self, dirs):
        dirs.extend(
            {'path': path, 'recursive': True, 'ignores': ['*/__pycache__*']}
            for path in self.module_manager.module_dirs
        )

    @event_handler('dir_change')
    def dir_change(self, event):
        module_paths = {
            os.path.realpath(module.__file__): name
            for name, (module, _) in self.module_manager._modules.items()
        }

        best_path = pathext.longest_prefix(
            os.path.realpath(event.src_path),
            module_paths.keys()
        )

        if best_path in module_paths:
            # One module changed
            self.logger.info("Module `{}` changed"
                             .format(module_paths[best_path]))
            self.module_manager.reload(module_paths[best_path])
        else:
            # New module
            self.logger.info("New module added with path=`{}`"
                             .format(event.src_path))
            self.module_manager.load_all()
