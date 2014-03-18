#! /usr/bin/env python3
from sshm.lib import sshm

import os
import os.path
import tempfile
import unittest

@unittest.skipIf('CI' in os.environ.keys(), 'Travis-CI is running these tests.')
class TestReal(unittest.TestCase):
    """
    You must be able to login to your own machine for these tests to work.
    """

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
        results_list = list(sshm('localhost', 'exit'))
        result = results_list[0]
        self.assertEqual(0, result['return_code'])


    def test_localhost_nonzero(self):
        """
        Simply login to the local machine and exit with a non-zero.
        """
        results_list = list(sshm('localhost', 'exit 1'))
        result = results_list[0]
        self.assertEqual(1, result['return_code'])


    def test_localhost_stdin(self):
        """
        Login to the local machine and pass a file object through stdin.
        """
        contents = b'hello'
        fh = self._get_temp_file(contents)

        results_list = list(sshm('localhost', 'cat', stdin=fh))
        result = results_list[0]
        self.assertEqual(result['return_code'], 0)
        self.assertEqual('hello', result['stdout'])
        # We expect a unicode string.  Python3.x's strings are unicode.
        try:
            self.assertIsInstance(result['stdout'], unicode)
        except NameError:
            self.assertIsInstance(result['stdout'], str)


    def test_localhost_multi(self):
        """
        Simply login to the local machine three times and verify there is
        output.
        """
        results_list = list(sshm('localhost,localhost,localhost', 'echo testing'))

        # Verify all instances are unique
        self.assertEqual(3,
                len(results_list))

        for result in results_list:
            self.assertEqual(0, result['return_code'])
            self.assertEqual('testing\n', result['stdout'])


    def test_binary_copy(self):
        """
        Binary files are transfered correctly using STDIN.
        """
        contents = os.urandom(10000)
        fh = self._get_temp_file(contents)

        tfh = tempfile.NamedTemporaryFile()

        results_list = list(sshm('localhost', 'cat > %s' % tfh.name, stdin=fh))
        result = results_list[0]
        self.assertEqual(0, result['return_code'])

        self.assertTrue(os.path.isfile(tfh.name))

        # Read the contents of the copied file, make sure they are intact.
        with open(tfh.name, 'rb') as tfh:
            self.assertEqual(tfh.read(), contents)



