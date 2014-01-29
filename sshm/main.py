#! /usr/bin/env python3
try:
    from lib import sshm
    from lib import get_argparse_args
except ImportError:
    from sshm.lib import sshm
    from sshm.lib import get_argparse_args

__all__ = ['SSHHandle', 'method_results_gatherer', 'sshm']

def main():
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
        out = ['sshm: %s%s(%d):' % (
                'Failure: ' if result['return_code'] != 0 else '',
                result['url'],
                result['return_code'],
                ),]
        if result['traceback']: out.append(result['traceback'].rstrip('\n'))
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


if __name__ == '__main__':
    main()

