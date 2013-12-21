#! /usr/bin/env python3
from sshm import *

import os
import os.path
import tempfile
import unittest

# Skip the real tests if travis-ci.org is running the tests
try:
    os.environ['CI']
    skip_if_ci = 'travis-ci.org is running these tests'
except KeyError:
    skip_if_ci = ''

@unittest.skipIf('CI' in os.environ.keys(), 'Travis-CI is running these tests.')
class TestReal(unittest.TestCase):
    """
    You must be able to login to your own machine for these tests to work.
    """

    skip = skip_if_ci

    def _get_temp_file(self, contents):
        """
        Create a temporary file, write contents to it, and return a readable
        tempfile handle.
        """
        fh = tempfile.NamedTemporaryFile('wb', delete=False)
        name = fh.name
        fh.write(contents)
        fh.seek(0)
        fh.close()
        fh = open(name, 'r')
        return fh


    def test_localhost(self):
        """
        Simply login to the local machine and exit.
        """
        results_list = sshm('localhost', 'exit')
        success, instance, results = results_list[0]
        self.assertEqual(True, success)


    def test_localhost_nonzero(self):
        """
        Simply login to the local machine and exit with a non-zero.
        """
        results_list = sshm('localhost', 'exit 1')
        success, instance, results = results_list[0]
        self.assertEqual(False, success)


    def test_localhost_stdin(self):
        """
        Login to the local machine and pass a file object through stdin.
        """
        contents = b'hello'
        fh = self._get_temp_file(contents)

        results_list = sshm('localhost', 'cat', stdin=fh)
        success, instance, message = results_list[0]
        self.assertTrue(success, message)
        self.assertEqual('hello', message)
        # We expect a unicode string.  Get the type of unicode string to avoid
        # python renaming issues.
        self.assertIsInstance(message, type(u'')


    def test_localhost_multi(self):
        """
        Simply login to the local machine three times and verify there is
        output.
        """
        results_list = sshm('localhost,localhost,localhost', 'echo testing')

        # Verify all instances are unique
        assert len(set([i for ign, i, ign in results_list])) == 3

        for success, instance, results in results_list:
            self.assertEqual(True, success)
            self.assertEqual('testing\n', results)


    def test_binary_copy(self):
        """
        Binary files are transfered correctly using STDIN.
        """
        contents = os.urandom(10000)
        fh = self._get_temp_file(contents)

        tfh = tempfile.NamedTemporaryFile()

        results_list = sshm('localhost', 'cat > %s' % tfh.name, stdin=fh)
        success, instance, results = results_list[0]
        self.assertTrue(success, results)

        self.assertTrue(os.path.isfile(tfh.name))

        # Read the contents of the copied file, make sure they are intact.
        with open(tfh.name, 'rb') as tfh:
            self.assertEqual(tfh.read(), contents)



if __name__ == '__main__':
    unittest.main()
