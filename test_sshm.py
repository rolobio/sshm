#! /usr/bin/env python3
from sshm import *

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
            output = EXTRACT_URIS.findall(uris)
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
            output = PARSE_URI.match(uri).groups('')
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
            output = expand_ranges(range_str)
            self.assertEqual(expected, output)


    def test_expand_servers(self):
        tests = [
            ('example.com',
                [('example.com', '22')],
            ),
            ('mail.example.com',
                [('mail.example.com', '22')],
            ),
            ('example.com,mail.example.com',
                [('example.com', '22'),
                ('mail.example.com', '22')
                ],
            ),
            ('mail.exa_mple3.com',
                [('mail.exa_mple3.com', '22')],
            ),
            ('mail[1-3].example.com',
                [('mail1.example.com', '22'),
                ('mail2.example.com', '22'),
                ('mail3.example.com', '22'),
                ],
            ),
            ('mail[1-3].example.com,example[5-7,9].com',
                [('mail1.example.com', '22'),
                ('mail2.example.com', '22'),
                ('mail3.example.com', '22'),
                ('example5.com', '22'),
                ('example6.com', '22'),
                ('example7.com', '22'),
                ('example9.com', '22'),
                ],
            ),
        ]
        for servers_str, expected_list in tests:
            output = expand_servers(servers_str)
            assert len(output) == len(expected_list), \
                'Expected is not a long as output. Add more to the test.'
            for uri, expected in zip(output, expected_list):
                uri, port = uri
                expected_uri, expected_port = expected

                self.assertEqual(expected_uri, uri)
                self.assertEqual(expected_port, port)


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
        import tempfile
        import os

        # Create a temporary file to pass as stdin
        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write('hello')
        fh.seek(0)
        name = fh.name
        fh.close()
        fh = open(name, 'r')

        try:
            results_list = sshm('localhost', 'cat', stdin=fh)
            success, instance, results = results_list[0]
            self.assertEqual(True, success)
            self.assertEqual('hello', results)
            # We expect a utf-8 string as output
            self.assertIsInstance(results, str)
        except: raise
        finally:
            fh.close()
            os.remove(fh.name)


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



if __name__ == '__main__':
    unittest.main()

