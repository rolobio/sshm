#! /usr/bin/env python3
"""
This module tests the basic functionality of sshm without performing a real ssh
command.
"""
from sshm import lib

from mock import MagicMock
import unittest
import zmq


class TestFuncs(unittest.TestCase):


    def test_uri_expansion(self):
        """
        The target specification should match Nmap's capabilities.

        Example:
            10.1.2.3,user@192.168.0.1-254,10.0.2-4,0-255,mail[01-5].example.com:1234
            [
               '10.1.2.3',
               'user@192.168.0.1', ...  'user@192.168.0.254',
               '10.0.2.0', ...  '10.0.2.255',
               '10.0.3.0', ...  '10.0.3.255',
               '10.0.4.0', ...  '10.0.4.255',
               'mail01.example.com:1234',
               'mail02.example.com:1234',
               'mail03.example.com:1234',
               'mail04.example.com:1234',
               'mail05.example.com:1234',
           ]
        """
        prov_exp = [
                # IPs
                ('10.1.2.3', ['10.1.2.3']),
                ('10.1.2.3:123', ['10.1.2.3:123']),
                ('10.2.3.4,example.com', ['10.2.3.4', 'example.com']),
                ('10.4.5.6-8', ['10.4.5.6', '10.4.5.7', '10.4.5.8']),
                ('10-11.1.2.3', ['10.1.2.3', '11.1.2.3']),
                ('10-11.1.2.3-5',['10.1.2.3', '10.1.2.4', '10.1.2.5', '11.1.2.3', '11.1.2.4', '11.1.2.5']),
                ('192.168.3-5,7.1', ['192.168.3.1', '192.168.4.1', '192.168.5.1', '192.168.7.1']),
                ('192.168.3-5,7.1:567', ['192.168.3.1:567', '192.168.4.1:567', '192.168.5.1:567', '192.168.7.1:567']),
                ('192.168.0.-', ['192.168.0.%d' % i for i in range(0,256)]),
                # URLs
                ('example.com', ['example.com']),
                ('example.com:789', ['example.com:789']),
                ('user@example.com', ['user@example.com']),
                ('mail[01-3].example.com', ['mail01.example.com', 'mail02.example.com', 'mail03.example.com']),
                ('mail[01-3].example.com:123', ['mail01.example.com:123', 'mail02.example.com:123', 'mail03.example.com:123']),
                ('ex-ample.com', ['ex-ample.com',]),
                ('root@ex-ample.com', ['root@ex-ample.com',]),
                # Combinations
                ('example.com,1.2.3.4', ['example.com', '1.2.3.4']),
                ('root@example.com:1234,root@1.2.3.4:1234', ['root@example.com:1234', 'root@1.2.3.4:1234']),
                ('foo@example[11-13,17].com:1234,root@1.2,5-7.3.4:1234', ['foo@example11.com:1234', 'foo@example12.com:1234', 'foo@example13.com:1234', 'foo@example17.com:1234', 'root@1.2.3.4:1234', 'root@1.5.3.4:1234', 'root@1.6.3.4:1234', 'root@1.7.3.4:1234']),
                ('10.1.1.1,10.1.1.2', ['10.1.1.1', '10.1.1.2']),
                ('10.1.1.1,3,10.1.1.5', ['10.1.1.1', '10.1.1.3', '10.1.1.5']),
                ('10.1.1.1,3,10.1.1.5,root@example[01-2].com,10-11.1.1.1-5', ['10.1.1.1', '10.1.1.3', '10.1.1.5', 'root@example01.com', 'root@example02.com', '10.1.1.1', '10.1.1.2', '10.1.1.3', '10.1.1.4', '10.1.1.5', '11.1.1.1', '11.1.1.2', '11.1.1.3', '11.1.1.4', '11.1.1.5']),
                ]

        for provided, expected in prov_exp:
            self.assertEqual(lib.uri_expansion(provided),
                    expected)

    def test_invalid_uri_expansion(self):
        """
        Invalid expansions should raise an Exception.
        """
        prov = [
                '10.1.2.3-2',
                '10.2',
                'example[2-1].com',
                '',
                None
                ]

        for provided in prov:
            self.assertRaises(ValueError, lib.uri_expansion, provided)


    def test_expand_ranges(self):
        """
        This function should convert a string of comma and dash seperated
        integers and convert them into a list of number strings.
        """
        tests = [
            ('1', ['1',]),
            ('10', ['10',]),
            ('01', ['01',]),
            ('01-06', ['01', '02', '03', '04', '05', '06']),
            ('01-03,7', ['01', '02', '03', '7']),
            ('5-7,9', ['5', '6', '7', '9']),
            ('003-006', ['003', '004', '005', '006']),
            ('1,01,05-8,0006-0008,12,100', ['1', '01', '05', '06', '07', '08', '0006', '0007', '0008', '12', '100']),
        ]

        for range_str, expected in tests:
            output = lib.expand_ranges(range_str)
            self.assertEqual(expected, output)




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
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen

        context, socket = fake_context()
        lib.ssh(1, context, 'foo:9678', 'command', [])

        # Get the result that was sent in the socket
        self.assertEqual(socket.send_pyobj.call_count, 1)
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo', '-p', '9678', 'command'])


    def test_exception(self):
        """
        An exception is passed in the results.
        """
        sub, proc = fake_subprocess('', '', 0)
        proc.communicate.side_effect = Exception('Oh no!')
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen

        context, socket = fake_context()
        lib.ssh(1, context, 'foo', '9678', 'command', [])
        results = socket.send_pyobj.call_args_list[0][0][0]

        self.assertIn('traceback', results)
        self.assertIn('Oh no!', results['traceback'])


    def test_formatting(self):
        """
        A dictionary of unique strings are provided to use when formatting
        the command string.
        """
        sub, proc = fake_subprocess('', '', 0)
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen
        context, socket = fake_context()

        # No formatting in the command string
        lib.ssh(1, context, 'foo', 'command', [])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo', 'command'])
        socket.reset_mock()

        # URI in formatting
        lib.ssh(1, context, 'foo', 'command{uri}', [])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo', 'commandfoo'])
        socket.reset_mock()

        # FQDN in formatting
        lib.ssh(1, context, 'www.foo.com:22', 'command{fqdn}', [])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'www.foo.com', '-p', '22', 'commandwww.foo.com'])
        socket.reset_mock()

        # Subdomain in formatting
        lib.ssh(1, context, 'foo.example.com', 'command{subdomain}', [])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo.example.com', 'commandfoo'])
        socket.reset_mock()

        # Multiple formatting
        lib.ssh(1, context, 'foo.example.com:8888', 'command {subdomain} {fqdn} {uri}', [])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo.example.com', '-p', '8888',
                    'command foo foo.example.com foo.example.com:8888'])
        socket.reset_mock()

        # Bad formatting
        lib.ssh(1, context, 'foo', 'command{bad}', [])
        self.assertIn('traceback', socket.send_pyobj.call_args_list[0][0][0])
        socket.reset_mock()

        # Disable formatting
        self.addCleanup(setattr, lib, 'disable_formatting', lib.disable_formatting)
        lib.disable_formatting = True
        lib.ssh(1, context, 'foo', 'command{bad}', [])
        self.assertNotIn('traceback', socket.send_pyobj.call_args_list[0][0][0])
        cmd = socket.send_pyobj.call_args_list[0][0][0]['cmd']
        self.assertEqual(cmd,
                ['ssh', 'foo', 'command{bad}'])
        socket.reset_mock()



class Test_sshm(unittest.TestCase):

    def test_simple(self):
        """
        Test a simple sshm usage.
        """
        sub, proc = fake_subprocess('', '', 0)
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen

        result_list = list(lib.sshm('example.com', 'exit'))
        self.assertEqual(1, len(result_list))
        self.assertEqual(result_list[0],
                {
                    'stdout': '',
                    'uri': 'example.com',
                    'cmd': ['ssh', 'example.com', 'exit'],
                    'return_code': 0,
                    'stderr': '',
                    'thread_num':0,
                    }
                )


    def test_stdin(self):
        """
        Test the STDIN sending process between sshm and ssh.
        """
        sub, proc = fake_subprocess('', '', 0)
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen

        # Fake the process's poll to be None once
        c = [1, None]
        def none_once():
            return c.pop()
        proc.poll = none_once

        from io import BytesIO
        stdin_contents = b'foobar'
        stdin = BytesIO(stdin_contents)

        result_list = list(lib.sshm('example.com', 'exit', stdin=stdin))
        self.assertEqual(1, len(result_list))
        self.assertEqual(result_list[0],
                {
                    'stdout': '',
                    'uri': 'example.com',
                    'cmd': ['ssh', 'example.com', 'exit'],
                    'return_code': 0,
                    'stderr': '',
                    'thread_num':0,
                    }
                )


    def test_triple(self):
        """
        You can SSH into three servers at once.
        """
        sub, proc = fake_subprocess('', '', 0)
        self.addCleanup(setattr, lib, 'popen', lib.popen)
        lib.popen = sub.popen

        results_list = list(lib.sshm('example[01-03].com', 'exit'))
        self.assertEqual(3, len(results_list))
        self.assertEqual(3,
                len(set([r['uri'] for r in results_list]))
                )
        for result in results_list:
            self.assertNotIn('traceback', result)
            self.assertIn(result['uri'],
                    ['example01.com', 'example02.com', 'example03.com']
                    )


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
        self.addCleanup(setattr, lib, 'ssh', lib.ssh)
        lib.ssh = MagicMock(side_effect=side_effect)

        from io import BytesIO
        stdin_contents = b'stdin contents'
        stdin = BytesIO(stdin_contents)

        extra_arguments = ['-o=Something yes',]
        result_list = list(lib.sshm('example[01-03].com', 'foo',
            extra_arguments=extra_arguments, stdin=stdin))

        for result in result_list:
            self.assertIn('thread_num', result)

        expected_uris = [
                'example01.com',
                'example02.com',
                'example03.com',
                ]

        self.assertTrue(lib.ssh.called)
        # Verify each ssh function call
        self.assertEqual(len(lib.ssh.call_args_list), len(expected_uris))
        for args_list, expected_uri in zip(lib.ssh.call_args_list, expected_uris):
            args, kwargs = args_list

            self.assertEqual(kwargs, {})

            thread_num, context, uri, command, extra_arguments, stdin = args
            self.assertEqual(int, type(thread_num))
            self.assertEqual(zmq.Context, type(context))
            self.assertEqual(expected_uri, uri)
            self.assertEqual('foo', command)
            self.assertEqual(extra_arguments, extra_arguments)
            self.assertTrue(stdin)



