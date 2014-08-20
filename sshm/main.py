#! /usr/bin/env python3
"""
This module allows the console to use SSHM's functionality.

This module should only be run by the console!
"""

from __future__ import print_function
import sys
try: # pragma: no cover version specific
    from lib import sshm
except ImportError: # pragma: no cover version specific
    from sshm.lib import sshm

__all__ = ['main']


def get_argparse_args(args=None):
    """
    Get the arguments passed to this script when it was run.

    @param args: A list of arguments passed in the console.
    @type args: list

    @returns: A tuple containing (args, command, extra_args)
    @rtype: tuple
    """
    try: # pragma: no cover
        from _info import __version__, __long_description__
    except ImportError: # pragma: no cover
        from sshm._info import __version__, __long_description__
    import argparse

    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=__long_description__)
    parser.add_argument('servers')
    parser.add_argument('command')
    parser.add_argument('-s', '--sorted-output', action='store_true', default=False,
            help='Sort the output by the URI of each instance.  This will wait for all instances to finish before showing any output!')
    parser.add_argument('-p', '--strip-whitespace', action='store_true', default=False,
            help='Remove any whitespace surrounding the output of each instance.')
    parser.add_argument('--version', action='version', version='%(prog)s '+__version__)
    args, extra_args = parser.parse_known_args(args=args)
    return (args, args.command, extra_args)


def _print_handling_newlines(uri, return_code, to_print, header='', strip_whitespace=False, file=sys.stdout):
    """
    Print "to_print" to "file" with the formatting needed to represent it's data
    properly.
    """
    if strip_whitespace:
        to_print = to_print.strip()
    if to_print.count('\n') == 0:
        sep = ' '
    else:
        sep = '\n'
    print('sshm: {}{}({}):{}{}'.format(header, uri, return_code, sep, to_print), file=file)


def main():
    """
    Run SSHM using console provided arguments.

    This should only be run using a console!
    """
    import select
    args, command, extra_arguments = get_argparse_args()

    # Only provided stdin if there is data
    r_list, i, i = select.select([sys.stdin], [], [], 0)
    if r_list:
        stdin = r_list[0]
    else:
        stdin = None

    # Perform the command on each server, print the results to stdout.
    results = sshm(args.servers, command, extra_arguments, stdin)
    # If a sorted output is requested, gather all results before output.
    if args.sorted_output:
        results = list(results)
        results = sorted(results, key=lambda x: x['uri'])

    for result in results:
        if result.get('stdout') != None:
            _print_handling_newlines(result['uri'],
                    result['return_code'],
                    result['stdout'],
                    strip_whitespace=args.strip_whitespace,
                    )
        if result.get('stderr'):
            _print_handling_newlines(result['uri'],
                    result.get('return_code', ''),
                    result['stderr'],
                    'Error: ',
                    strip_whitespace=args.strip_whitespace,
                    file=sys.stderr,
                    )
        if result.get('traceback'):
            _print_handling_newlines(result['uri'],
                    result['traceback'],
                    'Traceback: ',
                    strip_whitespace=args.strip_whitespace,
                    file=sys.stderr,
                    )

    # Exit with non-zero when there is a failure
    if sum([r['return_code'] for r in results]):
        sys.exit(1)


if __name__ == '__main__':
    main()

