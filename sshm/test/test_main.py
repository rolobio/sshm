#! /usr/bin/env python3
"""
This module tests what is testable in main.py
"""
from sshm.main import get_argparse_args, _print_handling_newlines

from mock import MagicMock
import unittest
try:
    # Python2.7
    from StringIO import StringIO
except ImportError:
    # Python 3+
    from io import StringIO


class TestFuncs(unittest.TestCase):

    def test_get_argparse_args(self):
        """
        Simple examples of how the console should react to certain arguments.
        """
        # Valid
        provided = ['example.com', 'ls']
        args, command, extra_args = get_argparse_args(provided)
        self.assertEqual(args.servers, 'example.com')
        self.assertEqual(command, 'ls')
        self.assertEqual(extra_args, [])

        # Valid
        provided = ['example[1-3].com', 'exit']
        args, command, extra_args = get_argparse_args(provided)
        self.assertEqual(args.servers, 'example[1-3].com')
        self.assertEqual(command, 'exit')
        self.assertEqual(extra_args, [])

        # Lack of required arguments
        provided = ['example.com']
        self.assertRaises(SystemExit, get_argparse_args, provided)
        provided = []
        self.assertRaises(SystemExit, get_argparse_args, provided)

        # Extra arguments
        provided = ['example[1-3].com', 'exit', '-o UserKnownHostsFile=/dev/null']
        args, command, extra_args = get_argparse_args(provided)
        self.assertEqual(args.servers, 'example[1-3].com')
        self.assertEqual(command, 'exit')
        self.assertEqual(extra_args, [provided[2],])


    def test__print_handling_newlines(self):
        """
        This function should format the output as needed.
        """
        prov_exp = [
                (('', '', ''), 'sshm: (): \n'),
                (('uri', 'return_code', 'to_print'), 'sshm: uri(return_code): to_print\n'),
                (('uri', 'return_code', 'to_print', 'header'), 'sshm: headeruri(return_code): to_print\n'),
                (('uri', 'return_code', 'to_print\n', 'header: '), 'sshm: header: uri(return_code):\nto_print\n\n'),
                ]

        for provided, expected in prov_exp:
            tfh = StringIO()
            _print_handling_newlines(*provided, file=tfh),
            tfh.seek(0)
            self.assertEqual(tfh.read(), expected)



