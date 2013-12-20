#!/usr/bin/env python3
import argparse
import sys
import unittest

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-v', action='count', default=1,
            help='Increase verbosity')
    args = p.parse_args()

    tests = unittest.TestLoader().discover('sshm/test')
    runner = unittest.TextTestRunner(verbosity=args.v)
    result = runner.run(tests)
    sys.exit(not result.wasSuccessful())

