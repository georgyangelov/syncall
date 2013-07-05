import os
import sys
import logging


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

import syncall


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
console_handler.setLevel(logging.DEBUG)

formatter = ConsoleFormatter()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


# Add custom logging for console
def log_console(self, message, *args, **kws):
    if self.isEnabledFor(LEVEL_CONSOLE_LOG):
        self._log(LEVEL_CONSOLE_LOG, message, args, **kws)
logging.Logger.console = log_console

# End logging config

CONFIG_DIR = os.environ['HOME'] + '/.syncall'
SHARE_DIR = CONFIG_DIR + '/shared/'

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(SHARE_DIR, exist_ok=True)

uuid = syncall.get_uuid(CONFIG_DIR + '/.uuid')

share_dir_obj = syncall.Directory(uuid, SHARE_DIR,
                                  create_temp_dir=True)
share_dir_obj.update_index()

network_discovery = syncall.NetworkDiscovery(
    syncall.DEFAULT_PORT,
    syncall.VERSION,
    uuid
)
network_discovery.start_listening()

connection_listener = syncall.ConnectionListener(
    uuid,
    syncall.DEFAULT_PORT
)
transfer_listener = syncall.ConnectionListener(
    uuid,
    syncall.DEFAULT_TRANSFER_PORT
)

store_manager = syncall.RemoteStoreManager(
    network_discovery,
    connection_listener,
    transfer_listener,
    share_dir_obj,
    uuid
)

connection_listener.start()
transfer_listener.start()


def shutdown():
    """ Stop the listener threads and remote connections on shutdown """
    network_discovery.shutdown()
    connection_listener.shutdown()
    transfer_listener.shutdown()
    store_manager.shutdown()
    share_dir_obj.clear_temp_dir()


try:
    while True:
        cmd = input()

        if cmd.lower() in ('exit', 'quit', 'x', 'q'):
            break
        elif len(cmd) == 0:
            continue
        elif cmd.lower() == 'scan':
            network_discovery.request()
        elif cmd.lower() == 'index':
            share_dir_obj.update_index(force=True)

            print(share_dir_obj._index)
            print(
                "Total number of files: {}"
                .format(len(share_dir_obj._index))
            )
        elif cmd.lower() == 'showindex':
            print(share_dir_obj._index)
            print(
                "Total number of files: {}"
                .format(len(share_dir_obj._index))
            )
        else:
            print("Unknown command '" + cmd + "'")
finally:
    shutdown()
