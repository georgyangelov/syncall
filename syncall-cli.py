import os
import sys
import logging

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

from pymodules import ModuleManager

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.CONSOLE = LEVEL_CONSOLE_LOG = 15
logging.addLevelName(LEVEL_CONSOLE_LOG, "CONSOLE")


# Custom formatter for console logging
class ConsoleFormatter(logging.Formatter):
    console_format = "%(message)s"
    d_format = "%(levelname)-5s | %(name)-23s | %(funcName)-13s | %(message)s"

    def format(self, record):
        if record.levelno == LEVEL_CONSOLE_LOG:
            self._style._fmt = self.console_format
        else:
            self._style._fmt = self.d_format

        return super().format(record)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.CONSOLE)

formatter = ConsoleFormatter()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


# Add custom logging for console
def log_console(self, message, *args, **kws):
    if self.isEnabledFor(LEVEL_CONSOLE_LOG):
        self._log(LEVEL_CONSOLE_LOG, message, args, **kws)
logging.Logger.console = log_console

# End logging config

module_manager = ModuleManager([CURRENT_DIR + '/modules'])
module_manager.load_all()

module_manager.event_manager.notify('app_start', {
    'cwd': CURRENT_DIR,
    'modules': module_manager.get_modules()
})

while True:
    cmd = input('~> ')

    if cmd.lower() in ('exit', 'quit', 'x', 'q'):
        break
    elif len(cmd) == 0:
        continue
    else:
        is_not_handled = module_manager.event_manager.notify('app_cmd', {
            'cmd': cmd
        })

        if is_not_handled:
            print("Unknown command '" + cmd + "'")
