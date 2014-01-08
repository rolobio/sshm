import unittest
import sys

print('Python version: %s' % str(sys.version_info))

suite = unittest.TestLoader().discover('.')
