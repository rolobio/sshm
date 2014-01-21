#! /usr/bin/env python3
from sshm import lib

from mock import MagicMock, call
import unittest

class TestRegex(unittest.TestCase):

    def test_EXTRACT_URIS(self):
        tests = [
            ('example.com',
                ['example.com'],
            ),
            ('example.com,example2.com',
                ['example.com', 'example2.com'],
            ),
            ('mail.example.com',
                ['mail.example.com'],
            ),
            ('user@example.com:500',
                ['user@example.com:500'],
            ),
            ('user.name@example.com',
                ['user.name@example.com'],
            ),
            ('user@example.com:500,exam_ple.com',
                ['user@example.com:500', 'exam_ple.com'],
            ),
        ]

        for uris, expected in tests:
            output = lib.EXTRACT_URIS.findall(uris)
            self.assertEqual(expected, output)


    def test_PARSE_URI(self):
        tests = [
            ('example.com',
                ('', 'example.com', '', '', '')
            ),
            ('user@example.com',
                ('user', 'example.com', '', '', '')
            ),
            ('user@example.com:500',
                ('user', 'example.com', '', '', '500')
            ),
            ('example[1-5].com',
                ('', 'example', '1-5', '.com', '')
            ),
            ('user@example[1-5].com:22',
                ('user', 'example', '1-5', '.com', '22')
            ),
        ]

        for uri, expected in tests:
            output = lib.PARSE_URI.match(uri).groups('')
            self.assertEqual(expected, output)



class TestRegexFuncs(unittest.TestCase):

    def test_expand_ranges(self):
        tests = [
            ('1',
                ['1',],
            ),
            ('10',
                ['10',],
            ),
            ('01',
                ['01',],
            ),
            ('01-06',
                ['01', '02', '03', '04', '05', '06'],
            ),
            ('01-03,7',
                ['01', '02', '03', '7'],
            ),
            ('5-7,9',
                ['5', '6', '7', '9'],
            ),
            ('003-006',
                ['003', '004', '005', '006'],
            ),
            ('1,01,05-8,0006-0008,12,100',
                ['1', '01', '05', '06', '07', '08', '0006', '0007', '0008', '12', '100'],
            ),
        ]

        for range_str, expected in tests:
            output = lib.expand_ranges(range_str)
            self.assertEqual(expected, output)


    def test_expand_servers(self):
        tests = [
            ('example.com',
                [('example.com', '')],
                ),
            ('mail.example.com',
                [('mail.example.com', '')],
                ),
            ('example.com,mail.example.com',
                [('example.com', ''),
                ('mail.example.com', '')
                ],
                ),
            ('mail.exa_mple3.com',
                [('mail.exa_mple3.com', '')],
                ),
            ('mail[1-3].example.com',
                [('mail1.example.com', ''),
                ('mail2.example.com', ''),
                ('mail3.example.com', ''),
                ],
                ),
            ('mail[1-3].example.com,example[5-7,9].com',
                [('mail1.example.com', ''),
                ('mail2.example.com', ''),
                ('mail3.example.com', ''),
                ('example5.com', ''),
                ('example6.com', ''),
                ('example7.com', ''),
                ('example9.com', ''),
                ],
                ),
            (
                'example[1-3].com:123',
                [
                    ('example1.com', '123'),
                    ('example2.com', '123'),
                    ('example3.com', '123'),
                    ],
                ),
            (
                'example[1-3].com:123,mail1.example.com:789',
                [
                    ('example1.com', '123'),
                    ('example2.com', '123'),
                    ('example3.com', '123'),
                    ('mail1.example.com', '789'),
                    ],
                ),
        ]
        for servers_str, expected_list in tests:
            output = lib.expand_servers(servers_str)
            assert len(output) == len(expected_list), \
                'Expected is not a long as output. Add more to the test.'
            for uri_port, expected in zip(output, expected_list):
                uri, port = uri_port
                expected_uri, expected_port = expected

                self.assertEqual(expected_uri, uri)
                self.assertEqual(expected_port, port)



class TestFuncs(unittest.TestCase):

    def test_get_argparse_args(self):
        # Valid
        provided = ['example.com', 'ls']
        args, command, extra_args = lib.get_argparse_args(provided)
        self.assertEqual(args.servers, 'example.com')
        self.assertEqual(command, 'ls')
        self.assertEqual(extra_args, [])

        # Valid
        provided = ['example[1-3].com', 'exit']
        args, command, extra_args = lib.get_argparse_args(provided)
        self.assertEqual(args.servers, 'example[1-3].com')
        self.assertEqual(command, 'exit')
        self.assertEqual(extra_args, [])

        # Lack of required arguments
        provided = ['example.com']
        self.assertRaises(SystemExit, lib.get_argparse_args, provided)
        provided = []
        self.assertRaises(SystemExit, lib.get_argparse_args, provided)

        # Extra arguments
        provided = ['example[1-3].com', 'exit', '-o UserKnownHostsFile=/dev/null']
        args, command, extra_args = lib.get_argparse_args(provided)
        self.assertEqual(args.servers, 'example[1-3].com')
        self.assertEqual(command, 'exit')
        self.assertEqual(extra_args, [provided[2],])



#class Testsshm(unittest.TestCase):
#
#    def test_simple(self):
#        """
#        Test a simple mocked case of using sshm.
#        """
#        return_value = {
#                'url':'example.com',
#                'stdout':'hello',
#                'exit_code':0,
#                }
#        lib.SSHHandle.execute = MagicMock(return_value=return_value)
#
#        # The command doesn't matter, the mocked ssh object will always
#        # return the return_value dict.
#        results = lib.sshm('example.com', 'foo')
#        self.assertEqual([return_value,], results)



class Test_ssh(unittest.TestCase):

    def fake_subprocess(self, stdout, stderr, returncode):
        proc = MagicMock()
        proc.returncode = returncode
        proc.communicate.return_value = (stdout, stderr)

        sub = MagicMock()
        sub.Popen.return_value = proc

        return (sub, proc)


    def fake_context(self):
        context = MagicMock()
        sock = MagicMock()
        context.socket.return_value = sock
        return context, sock


    def test_simple(self):
        """
        Simpliest usage of ssh
        """
        sub, proc = self.fake_subprocess('STDOUT', 'STDERR', 0)

        results = lib.ssh(None, None, None, 'url', None, 'command', False,
                None, subprocess=sub)

        # SSH command was constructed properly
        self.assertTrue(sub.Popen.called)
        self.assertEqual(sub.Popen.call_args[0],
                (['ssh', 'url', 'command'],)
                )

        # communicate was called
        self.assertTrue(proc.communicate.called)

        # Compare the results
        self.assertEqual(results,
                {
                    # Port is not present in command list
                    'cmd':['ssh', 'url', 'command'],
                    'port':None,
                    'return_code':0,
                    'stderr':u'STDERR',
                    'stdout':u'STDOUT',
                    'url':'url',
                    }
                )


    def test_port(self):
        """
        Port is only added when requested.
        """
        sub, proc = self.fake_subprocess('STDOUT', 'STDERR', 0)

        results = lib.ssh(None, None, None, 'url', 'PORT', 'command', False,
                None, subprocess=sub)

        self.assertEqual(results['cmd'],
                ['ssh', 'url', '-p', 'PORT', 'command'],
                )


    def test_extra_arguments(self):
        """
        Extra arguments are passed to the ssh command in the correct place.
        """
        sub, proc = self.fake_subprocess('STDOUT', 'STDERR', 0)

        results = lib.ssh(None, None, None, 'url', None, 'command', False,
                ['-N', '-D'], subprocess=sub)

        self.assertEqual(results['cmd'],
                ['ssh', '-N', '-D', 'url', 'command'],
                )


    def test_stdin(self):
        """
        ssh command requests the stdin contents using ZMQ
        """
        sub, proc = self.fake_subprocess('STDOUT', 'STDERR', 0)
        context, socket = self.fake_context()

        results = lib.ssh(context, None, None, 'url', None, 'command', True,
                None, subprocess=sub)

        self.assertTrue(context.socket.connect.called)
        self.assertTrue(context.socket.send_unicode.called)



