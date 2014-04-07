#! /usr/bin/env python3
"""
This module tests the basic functionality of sshm without performing a real ssh
command.
"""
from sshm import lib
from sshm.main import get_argparse_args

from mock import MagicMock
import unittest
import zmq


class TestTargetExpansion(unittest.TestCase):


    def test_is_url(self):
        """
        This is used to detect if a string contains alpha characters.
        """
        prov_exp = [
                ('a', True),
                ('example.com', True),
                ('mail1.example.com', True),
                ('10.1.2.3', False),
                ]

        for provided, expected in prov_exp:
            self.assertEqual(lib.is_url(provided), expected, provided)


    def test_target_expansion(self):
        """
        The target specification should match Nmap's capabilities.

        Example:
            10.1.2.3,192.168.0.1-254,10.0.2-4,0-255,mail[01-5].example.com:1234
            [
               '10.2.3.3',
               '192.168.0.1',
               '192.168.0.2',
               ...
               '192.168.0.254',
               '10.0.2.0',
               '10.0.2.1',
               ...
               '10.0.2.255',
               '10.0.3.0',
               '10.0.3.1',
               ...
               '10.0.3.255',
               '10.0.4.0',
               '10.0.j.1',
               ...
               '10.0.4.255',
               'mail01.example.com:1234',
               'mail02.example.com:1234',
               'mail03.example.com:1234',
               'mail04.example.com:1234',
               'mail05.example.com:1234',
           ]
        """
        prov_exp = [
                ('example.com', ['example.com']),
                ]

        for provided, expected in prov_exp:
            self.assertEqual(lib.target_expansion(provided),
                    expected)



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


    def test_create_uri(self):
        """
        create_uri assembles them as expected.
        """
        self.assertEqual('example.com',
                lib.create_uri('', 'example.com', '', '')
                )
        self.assertEqual('example01.com',
                lib.create_uri('', 'example', '01', '.com')
                )
        self.assertEqual('example01',
                lib.create_uri('', 'example', '01', '')
                )
        self.assertEqual('user@example',
                lib.create_uri('user', 'example', '', '')
                )
        self.assertEqual('user@example.com',
                lib.create_uri('user', 'example', '', '.com')
                )
        self.assertEqual('user@example10.com',
                lib.create_uri('user', 'example', '10', '.com')
                )



def fake_subprocess(stdout, stderr, returncode):
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate.return_value = (stdout, stderr)

    sub = MagicMock()
    sub.popen.return_value = proc

    return (sub, proc)


def fake_context():
    context = MagicMock()
    sock = MagicMock()
    context.socket.return_value = sock
    return context, sock


class Test_ssh(unittest.TestCase):
    """
    Test that the ssh function sends the correct command and returns the
    expected value.
    """

    def test_port(self):
        """
        The ssh command arguments change when a port is specified.
        """
        sub, proc = fake_subprocess('', '', 0)
        orig = lib.popen
        lib.popen = sub.popen

        context, socket = fake_context()
        lib.ssh(1, context, 'asdf', '9678', 'command', [])

        # Get the result that was sent in the socket
        self.assertEqual(socket.send_pyobj.call_count, 1)
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'asdf', '-p', '9678', 'command'])

        lib.popen = orig


    def test_exception(self):
        """
        An exception is passed in the results.
        """
        sub, proc = fake_subprocess('', '', 0)
        proc.communicate.side_effect = Exception('Oh no!')
        orig = lib.popen
        lib.popen = sub.popen

        context, socket = fake_context()
        lib.ssh(1, context, 'asdf', '9678', 'command', [])
        results = socket.send_pyobj.call_args_list[0][0][0]

        self.assertIn('traceback', results)
        self.assertIn('Oh no!', results['traceback'])

        lib.popen = orig



class Test_sshm(unittest.TestCase):

    def test_simple(self):
        """
        Test a simple sshm usage.
        """
        sub, proc = fake_subprocess('', '', 0)
        orig = lib.popen
        lib.popen = sub.popen

        result_list = list(lib.sshm('example.com', 'exit'))
        self.assertEqual(1, len(result_list))
        self.assertEqual(result_list[0],
                {
                    'stdout': '',
                    'url': 'example.com',
                    'cmd': ['ssh', 'example.com', 'exit'],
                    'return_code': 0,
                    'stderr': '',
                    'thread_num':0,
                    'port': ''
                    }
                )

        lib.popen = orig


    def test_triple(self):
        """
        You can SSH into three servers at once.
        """
        sub, proc = fake_subprocess('', '', 0)
        orig = lib.popen
        lib.popen = sub.popen

        results_list = list(lib.sshm('example[01-03].com', 'exit'))
        self.assertEqual(3, len(results_list))
        self.assertEqual(3,
                len(set([r['url'] for r in results_list]))
                )
        for result in results_list:
            self.assertNotIn('traceback', result)
            self.assertIn(result['url'],
                    ['example01.com', 'example02.com', 'example03.com']
                    )

        lib.popen = orig


class Test_sshm2(unittest.TestCase):


    def test_sshm_ssh(self):
        """
        Test how sshm uses the 'ssh' function.
        """
        def side_effect(thread_num, context, *a, **kw):
            """
            Send empty results.
            """
            sink = context.socket(zmq.PUSH)
            sink.connect(lib.SINK_URL)
            sink.send_pyobj({'thread_num':thread_num,})
        orig = lib.ssh
        lib.ssh = MagicMock(side_effect=side_effect)

        extra_arguments = ['-o=Something yes',]
        result_list = list(lib.sshm('example[01-03].com', 'foo',
            extra_arguments=extra_arguments))

        for result in result_list:
            self.assertIn('thread_num', result)

        expected_urls = [
                'example01.com',
                'example02.com',
                'example03.com',
                ]

        self.assertTrue(lib.ssh.called)
        # Verify each ssh function call
        self.assertEqual(len(lib.ssh.call_args_list), len(expected_urls))
        for args_list, expected_url in zip(lib.ssh.call_args_list, expected_urls):
            args, kwargs = args_list

            self.assertEqual(kwargs, {})

            thread_num, context, url, port, command, extra_arguments, stdin = args
            self.assertEqual(int, type(thread_num))
            self.assertEqual(zmq.Context, type(context))
            self.assertEqual(expected_url, url)
            self.assertEqual('', port)
            self.assertEqual('foo', command)
            self.assertEqual(extra_arguments, extra_arguments)
            self.assertEqual(type(stdin), type(memoryview(bytes())))

        lib.ssh = orig


