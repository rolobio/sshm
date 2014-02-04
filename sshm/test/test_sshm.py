#! /usr/bin/env python3
from sshm import lib
from sshm.main import get_argparse_args

from mock import MagicMock, call
import unittest
import zmq

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



class Test_sshm(unittest.TestCase):

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
        Test a simple sshm usage.
        """
        sub, proc = self.fake_subprocess('', '', 0)
        lib.Popen = sub.Popen

        result_list = list(lib.sshm('example.com', 'exit'))
        self.assertEqual(1, len(result_list))
        self.assertEqual(result_list[0],
                {
                    'traceback':'',
                    'stdout': '',
                    'url': 'example.com',
                    'cmd': ['ssh', 'example.com', 'exit'],
                    'return_code': 0,
                    'stderr': '',
                    'thread_num':0,
                    'port': ''
                    }
                )


    def test_triple(self):
        """
        You can SSH into three servers at once.
        """
        sub, proc = self.fake_subprocess('', '', 0)
        lib.Popen = sub.Popen

        results_list = list(lib.sshm('example[01-03].com', 'exit'))
        self.assertEqual(3, len(results_list))
        self.assertEqual(3,
                len(set([r['url'] for r in results_list]))
                )
        for result in results_list:
            self.assertEqual('', result['traceback'])
            self.assertIn(result['url'],
                    ['example01.com', 'example02.com', 'example03.com']
                    )


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
            sink.connect(lib.sink_url)
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
        for args_list, expected_url in zip(lib.ssh.call_args_list, expected_urls):
            args, kwargs = args_list

            self.assertEqual(kwargs, {})

            thread_num, context, url, port, command, extra_arguments = args
            self.assertEqual(int, type(thread_num))
            self.assertEqual(zmq.Context, type(context))
            self.assertEqual(expected_url, url)
            self.assertEqual('', port)
            self.assertEqual('foo', command)
            self.assertEqual(extra_arguments, extra_arguments)

        lib.ssh = orig


    def test_sshm_stdin(self):
        """
        sshm should pass the contents of stdin to any request on
        lib.requests_url.
        """
        import tempfile
        stdin_contents = b'foo'
        fh = tempfile.NamedTemporaryFile('wb', delete=False)
        fh.write(stdin_contents)
        fh.seek(0)
        fh = open(fh.name, 'r')

        def side_effect(thread_num, context, *a, **kw):
            sink = context.socket(zmq.PUSH)
            sink.connect(lib.sink_url)

            requests = context.socket(zmq.REQ)
            requests.connect(lib.requests_url)
            requests.send_unicode('get stdin')

            sink.send_pyobj({'stdin_contents':requests.recv_pyobj(), 'thread_num':thread_num})
        orig = lib.ssh
        lib.ssh = MagicMock(side_effect=side_effect)

        results_list = list(lib.sshm('example.com', 'exit', stdin=fh))
        self.assertEqual(results_list[0]['stdin_contents'], stdin_contents)



