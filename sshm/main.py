#! /usr/bin/env python3
try: # pragma: no cover version specific
    from lib import sshm
except ImportError: # pragma: no cover version specific
    from sshm.lib import sshm

__all__ = ['sshm']


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

    p = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=__long_description__)
    p.add_argument('servers')
    p.add_argument('command')
    p.add_argument('--version', action='version', version='%(prog)s '+__version__)
    args, extra_args = p.parse_known_args(args=args)
    return (args, args.command, extra_args)



def main(): # pragma: no cover
    """
    Run SSHM using console provided arguments.

    This should only be run using a console!
    """
    import select
    import sys
    args, command, extra_arguments = get_argparse_args()

    # Only provided stdin if there is data
    r_list, w_list, x_list = select.select([sys.stdin], [], [], 0)
    if r_list:
        stdin = r_list[0]
    else:
        stdin = None

    # Perform the command on each server, print the results to stdout.
    failure = False
    results = sshm(args.servers, command, extra_arguments, stdin)
    for result in results:
        if ('traceback' in result) and (result['traceback'] != ''):
            # An exception occured.
            out = ['sshm: Exception: %s:' % result['url'],
                    result['traceback'].rstrip('\n'),]
        else:
            out = ['sshm: %s%s(%d):' % (
                    'Failure: ' if result['return_code'] != 0 else '',
                    result['url'],
                    result['return_code'],
                    ),]
            if result['stdout']: out.append(result['stdout'].rstrip('\n'))
            if result['stderr']: out.append(result['stderr'].rstrip('\n'))
        # Put output in one line if it can fit
        if sum([s.count('\n') for s in out]) == 0 and len(out) <= 2:
            print(' '.join(out))
        else:
            # Too many newlines, print everything out on its own line
            for i in out:
                print(i)

    # Exit with non-zero when there is a failure
    if sum([r['return_code'] for r in results]):
        sys.exit(1)


if __name__ == '__main__': # pragma: no cover
    main()

