import os
import sys

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

from pyplugin import PluginManager

manager = PluginManager([CURRENT_DIR + '/plugins'])
manager.load_all()
