#! /usr/bin/env python3
from sshm import *

import os
import os.path
import tempfile
import unittest

class TestReal(unittest.TestCase):
    """
    You must be able to login to your own machine for these tests to work.
    """

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
        Simply login to the local machine and exit with a non-zero.
        """
        # Create a temporary file to pass as stdin
        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write('hello')
        fh.seek(0)
        name = fh.name
        fh.close()
        fh = open(name, 'r')

        try:
            results_list = sshm('localhost', 'cat', stdin=fh)
            success, instance, message = results_list[0]
            self.assertTrue(success, 'sshm was not successful')
            self.assertEqual('hello', message)
            # We expect a utf-8 string as output
            self.assertIsInstance(message, str)
        except: raise
        finally:
            if os.path.isfile(name):
                os.remove(name)


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
        fh = tempfile.NamedTemporaryFile('wb', delete=False)
        contents = os.urandom(10000)
        fh.write(contents)
        fh.seek(0)
        name = fh.name
        fh.close()
        fh = open(name, 'r')

        tmp_file = '/tmp/sshm_test'

        try:
            results_list = sshm('localhost', 'cat > %s' % tmp_file, stdin=fh)
            success, instance, results = results_list[0]
            self.assertTrue(success, results)

            self.assertTrue(os.path.isfile(tmp_file))

            # Read the contents of the copied file, make sure they are intact.
            with open(tmp_file, 'rb') as tfh:
                self.assertEqual(tfh.read(), contents)

        except: raise
        finally:
            if os.path.isfile(name):
                os.remove(name)
            if os.path.isfile(tmp_file):
                os.remove(tmp_file)



if __name__ == '__main__':
    unittest.main()
