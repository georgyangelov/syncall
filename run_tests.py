import os
import sys
import unittest
import logging

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_DIR + '/libs')

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)-5s | %(name)-23s | %(funcName)-13s | %(message)s"
)

if __name__ == '__main__':
    from tests.pymodules.all import *

    unittest.main()
