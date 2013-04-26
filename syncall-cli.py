import os
import sys

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

from pyplugin import PluginManager

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
    else:
        is_not_handled = plugin_manager.event_manager.notify('app_cmd', {
            'cmd': cmd
        })

        if is_not_handled:
            print("Unknown command '" + cmd + "'")
