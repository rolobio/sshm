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
                ('192.168.0.-', ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5', '192.168.0.6', '192.168.0.7', '192.168.0.8', '192.168.0.9', '192.168.0.10', '192.168.0.11', '192.168.0.12', '192.168.0.13', '192.168.0.14', '192.168.0.15', '192.168.0.16', '192.168.0.17', '192.168.0.18', '192.168.0.19', '192.168.0.20', '192.168.0.21', '192.168.0.22', '192.168.0.23', '192.168.0.24', '192.168.0.25', '192.168.0.26', '192.168.0.27', '192.168.0.28', '192.168.0.29', '192.168.0.30', '192.168.0.31', '192.168.0.32', '192.168.0.33', '192.168.0.34', '192.168.0.35', '192.168.0.36', '192.168.0.37', '192.168.0.38', '192.168.0.39', '192.168.0.40', '192.168.0.41', '192.168.0.42', '192.168.0.43', '192.168.0.44', '192.168.0.45', '192.168.0.46', '192.168.0.47', '192.168.0.48', '192.168.0.49', '192.168.0.50', '192.168.0.51', '192.168.0.52', '192.168.0.53', '192.168.0.54', '192.168.0.55', '192.168.0.56', '192.168.0.57', '192.168.0.58', '192.168.0.59', '192.168.0.60', '192.168.0.61', '192.168.0.62', '192.168.0.63', '192.168.0.64', '192.168.0.65', '192.168.0.66', '192.168.0.67', '192.168.0.68', '192.168.0.69', '192.168.0.70', '192.168.0.71', '192.168.0.72', '192.168.0.73', '192.168.0.74', '192.168.0.75', '192.168.0.76', '192.168.0.77', '192.168.0.78', '192.168.0.79', '192.168.0.80', '192.168.0.81', '192.168.0.82', '192.168.0.83', '192.168.0.84', '192.168.0.85', '192.168.0.86', '192.168.0.87', '192.168.0.88', '192.168.0.89', '192.168.0.90', '192.168.0.91', '192.168.0.92', '192.168.0.93', '192.168.0.94', '192.168.0.95', '192.168.0.96', '192.168.0.97', '192.168.0.98', '192.168.0.99', '192.168.0.100', '192.168.0.101', '192.168.0.102', '192.168.0.103', '192.168.0.104', '192.168.0.105', '192.168.0.106', '192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.110', '192.168.0.111', '192.168.0.112', '192.168.0.113', '192.168.0.114', '192.168.0.115', '192.168.0.116', '192.168.0.117', '192.168.0.118', '192.168.0.119', '192.168.0.120', '192.168.0.121', '192.168.0.122', '192.168.0.123', '192.168.0.124', '192.168.0.125', '192.168.0.126', '192.168.0.127', '192.168.0.128', '192.168.0.129', '192.168.0.130', '192.168.0.131', '192.168.0.132', '192.168.0.133', '192.168.0.134', '192.168.0.135', '192.168.0.136', '192.168.0.137', '192.168.0.138', '192.168.0.139', '192.168.0.140', '192.168.0.141', '192.168.0.142', '192.168.0.143', '192.168.0.144', '192.168.0.145', '192.168.0.146', '192.168.0.147', '192.168.0.148', '192.168.0.149', '192.168.0.150', '192.168.0.151', '192.168.0.152', '192.168.0.153', '192.168.0.154', '192.168.0.155', '192.168.0.156', '192.168.0.157', '192.168.0.158', '192.168.0.159', '192.168.0.160', '192.168.0.161', '192.168.0.162', '192.168.0.163', '192.168.0.164', '192.168.0.165', '192.168.0.166', '192.168.0.167', '192.168.0.168', '192.168.0.169', '192.168.0.170', '192.168.0.171', '192.168.0.172', '192.168.0.173', '192.168.0.174', '192.168.0.175', '192.168.0.176', '192.168.0.177', '192.168.0.178', '192.168.0.179', '192.168.0.180', '192.168.0.181', '192.168.0.182', '192.168.0.183', '192.168.0.184', '192.168.0.185', '192.168.0.186', '192.168.0.187', '192.168.0.188', '192.168.0.189', '192.168.0.190', '192.168.0.191', '192.168.0.192', '192.168.0.193', '192.168.0.194', '192.168.0.195', '192.168.0.196', '192.168.0.197', '192.168.0.198', '192.168.0.199', '192.168.0.200', '192.168.0.201', '192.168.0.202', '192.168.0.203', '192.168.0.204', '192.168.0.205', '192.168.0.206', '192.168.0.207', '192.168.0.208', '192.168.0.209', '192.168.0.210', '192.168.0.211', '192.168.0.212', '192.168.0.213', '192.168.0.214', '192.168.0.215', '192.168.0.216', '192.168.0.217', '192.168.0.218', '192.168.0.219', '192.168.0.220', '192.168.0.221', '192.168.0.222', '192.168.0.223', '192.168.0.224', '192.168.0.225', '192.168.0.226', '192.168.0.227', '192.168.0.228', '192.168.0.229', '192.168.0.230', '192.168.0.231', '192.168.0.232', '192.168.0.233', '192.168.0.234', '192.168.0.235', '192.168.0.236', '192.168.0.237', '192.168.0.238', '192.168.0.239', '192.168.0.240', '192.168.0.241', '192.168.0.242', '192.168.0.243', '192.168.0.244', '192.168.0.245', '192.168.0.246', '192.168.0.247', '192.168.0.248', '192.168.0.249', '192.168.0.250', '192.168.0.251', '192.168.0.252', '192.168.0.253', '192.168.0.254', '192.168.0.255']),
                # URLs
                ('example.com', ['example.com']),
                ('example.com:789', ['example.com:789']),
                ('user@example.com', ['user@example.com']),
                ('mail[01-3].example.com', ['mail01.example.com', 'mail02.example.com', 'mail03.example.com']),
                ('mail[01-3].example.com:123', ['mail01.example.com:123', 'mail02.example.com:123', 'mail03.example.com:123']),
                # Combinations
                ('example.com,1.2.3.4', ['example.com', '1.2.3.4']),
                ('root@example.com:1234,root@1.2.3.4:1234', ['root@example.com:1234', 'root@1.2.3.4:1234']),
                ('foo@example[11-13,17].com:1234,root@1.2,5-7.3.4:1234', ['foo@example11.com:1234', 'foo@example12.com:1234', 'foo@example13.com:1234', 'foo@example17.com:1234', 'root@1.2.3.4:1234', 'root@1.5.3.4:1234', 'root@1.6.3.4:1234', 'root@1.7.3.4:1234']),
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



