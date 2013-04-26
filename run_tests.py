import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

if __name__ == '__main__':
    from tests.pyplugin.all import *

    unittest.main()
