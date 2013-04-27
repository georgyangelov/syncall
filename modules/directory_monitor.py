import logging

from pymodules.Module import *


class DirectoryMonitor(Module):
    def __init__(self):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)

    def module_init(self):
        self.monitored_dirs = self.data_manager.request('monitor_dirs') or []

        print(self.monitored_dirs)
