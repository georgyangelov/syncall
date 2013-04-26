import os
import sys
import logging

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

from pyplugin import PluginManager

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] [%(name)s.%(funcName)s] -> %(message)s"
)

plugin_manager = PluginManager([CURRENT_DIR + '/plugins'])
plugin_manager.load_all()

plugin_manager.event_manager.notify('app_start', {
    'cwd': CURRENT_DIR,
    'plugins': plugin_manager.get_plugins()
})

while True:
    cmd = input('~> ')

    if cmd.lower() in ('exit', 'quit', 'x'):
        break
    elif len(cmd) == 0:
        continue
    else:
        is_not_handled = plugin_manager.event_manager.notify('app_cmd', {
            'cmd': cmd
        })

        if is_not_handled:
            print("Unknown command '" + cmd + "'")
