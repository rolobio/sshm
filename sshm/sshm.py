#! /usr/bin/env python3
import io
import re
import subprocess
import sys
import tempfile
import threading
import zmq


class SSHHandle(object):

    def __init__(self, uri, port):
        self.uri = uri
        self.port = port


    def execute(self, command, stdin=None, extra_arguments=None):
        """
        Perform an SSH command, pass it stdin.

        @type uri: str
        @param uri: The URI used to connect to a sepecific server.

        @type command: str
        @param command: Execute this one the remote server.

        @type stdin: bytes
        @param stdin: Pass these contents to ssh.
        """
        cmd = ['ssh',]
        # Add extra arguments after ssh, but before the uri and command
        if extra_arguments:
            cmd.extend(extra_arguments)
        # Only change the port at the user's request.  Otherwise, use SSH's
        # default port.
        if self.port:
            cmd.extend([self.uri, '-p', self.port, command])
        else:
            cmd.extend([self.uri, command])

        # Run the command, return its results
        proc = subprocess.Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate(input=stdin)
        return {'return_code':proc.returncode,
                'stdout':stdout.decode(),
                'stderr':stderr.decode(),
                }



def method_results_gatherer(instances, method_name, args, kwargs, stdin=None):
    """
    Execute the method named "method_name" on all instances with the
    arguments in args.

    @type instances: list
    @param instances: The instances whose methods will be executed.

    @type method_name: str
    @param method_name: Will be executed on each instance.

    @type args: tuple
    @param args: Arguments that will be passed to the method when called.

    @type kwargs: dict
    @param kwargs: A dictionary of keyword agruments that will be passed to
        the method when called.

    @type stdin: file
    @param stdin: A file containing data that will be passed to each ssh
        handle.

    @rtype: list
        Example:
            [
                {
                    'instance': Instance01('example01.com'),
                    'stdout': 'some stuff',
                    'stderr': None,
                    'return_code': 0,
                },
                {
                    'instance': Instance02('example02.com'),
                    'stdout': '',
                    'stderr': 'other stuff',
                    'return_code': 1,
                },
            ]
    """
    # Create the ZMQ connection
    context = zmq.Context()
    url = 'inproc://method_results_gatherer'
    conn = context.socket(zmq.REP)
    conn.bind(url)

    def _wrapper(instance, method_name, stdin, args, kwargs={}):
        """
        I perform a method and report what the method returns.
        """
        conn = context.socket(zmq.REQ)
        conn.connect(url)

        if stdin:
            # STDIN is available, get it
            conn.send_unicode('stdin')
            message = conn.recv_pyobj()
            kwargs['stdin'] = message

        try:
            # Get the method from the instance, run it with args
            method = getattr(instance, method_name)
            if type(args) in [list, tuple]:
                result = method(*args, **kwargs)
            else:
                result = method(args, **kwargs)
            # Attach the instance to the results
            result['instance'] = instance
            result['traceback'] = None
            # Notify the main thread that the result is ready
            conn.send_unicode('result')
            # throw away its reply
            conn.recv_unicode()
            # Send the result
            conn.send_pyobj(result)
        except Exception as e:
            # Exception occured, result an error
            conn.send_unicode('result')
            # throw away its reply
            conn.recv_unicode()
            # Send the error result
            conn.send_pyobj({
                'instance':instance,
                'stderr':e,
                'traceback':'TODO',
                'return_code': -1,
                })
        finally:
            conn.close()


    # Read the contents of STDIN. This will be passed to any thread that
    # makes a request.
    # We cannot pass stdin via a parameter.
    if stdin:
        if sys.version_info[:1] <= (2, 7):
            stdin_contents = stdin.read()
        else:
            stdin_contents = stdin.buffer.read()
        stdin.close()

    # Create the threads that will run each ssh connection
    threads = []
    if_stdin = True if stdin else False
    for instance in instances:
        thread = threading.Thread(target=_wrapper,
                args=(instance, method_name, if_stdin, args, kwargs))
        thread.start()
        threads.append(thread)

    # Respond to any requests for STDIN, gather all results and close
    finished_thread_count = 0
    results = []
    while finished_thread_count < len(threads):
        message = conn.recv_unicode()
        if message == 'result':
            # Thread has completed, get its result
            conn.send_unicode('result')
            # Get the results
            results.append(conn.recv_pyobj())
            # Thread closed
            finished_thread_count += 1
            # send close
            conn.send_unicode('close')
        elif message == 'stdin':
            # Thread requests stdin contents, send it
            conn.send_pyobj(stdin_contents)

    # All threads have closed, join them!
    for thread in threads:
        thread.join()

    conn.close()
    context.term()

    return results


MATCH_RANGES = re.compile(r'(?:(\d+)(?:,|$))|(?:(\d+-\d+))')
def expand_ranges(to_expand):
    """
    Convert a comma-seperated range of integers into a list. Keep any zero
    padding the numbers may have.

        Example: "1,4,07-10" to ['1', '4', '07', '08', '09', '10']

    @type ranges: str
    @param ranges: Expand this string into a list of integers.
    """
    nums = []
    for single, range_str in MATCH_RANGES.findall(to_expand):
        if single:
            nums.append(single)
        if range_str:
            x, y = range_str.split('-')
            # Create a string that will pad the integer with its current amount
            # of zeroes.
            # Example: if x is '03' the string will be '%0.2d'
            padding = '%'+'0.%d' % len(x) +'d'
            for i in range(int(x), int(y)+1):
                nums.append(padding % i)
    return nums


def create_uri(user, body, num, suffix, port):
    """
    Use the provided parameters to create a URI.  Port will be passed
    as the second object in the returned tuple.

    @rtype: tuple
        Example: ('user@host3', '22')
    """
    uri = ''
    if user: uri += user+'@'
    uri += body
    uri += num
    uri += suffix
    return (uri, port)


EXTRACT_URIS = re.compile(r'([@\w._:-]+(?:\[[\d,-]+\])?(?:[@\w._:-]+)?)(?:,|$)')
PARSE_URI = re.compile(r'(?:([\w._-]+)@)?(?:([\w._-]+)(?:\[([\d,-]+)\])?([\w._-]+)?)(?::([\d+]+))?$')
def expand_servers(server_list):
    """
    Create a URI tuple for each server in the list.

        Example: 'example[3-5].com,example7.com:245' to
            [
                ('example3.com', ''),
                ('example4.com', ''),
                ('example5.com' ''),
                ('example7.com', '245'),
            ]
    """
    uris = []
    for uri in EXTRACT_URIS.findall(server_list):
        # There should only be one URI in "uri", so we'll match it and get
        # the groups.
        user, body, range_str, suffix, port = PARSE_URI.match(uri).groups('')
        if range_str:
            # There are multiple hosts, add a URI for each
            for num in expand_ranges(range_str):
                uri = create_uri(user, body, num, suffix, port)
                uris.append(uri)
        else:
            uri = create_uri(user, body, '', suffix, port)
            uris.append(uri)
    return uris



def sshm(servers, command, extra_arguments=None, stdin=None):
    """
    SSH into multiple servers and execute "command". Pass stdin to these ssh
    handles.

    @param servers: A string containing the servers to execute "command" on via
        SSH.
        Examples:
            'example.com'
            'example[1-3].com'
            'mail[1,3,8].example.com'
    @type servers: str

    @param command: A string containing the command to execute.
    @type command: str

    @param extra_arguments: These arguments will be passed directly to each SSH
        subprocess instance.
    @type extra_arguments: list

    @param stdin: A file object that will be passed to each subproccess
        instance.
    @type stdin: file

    @returns: A list containing (success, handle, message) from each method
        call.
    """
    handles = [SSHHandle(*u) for u in expand_servers(servers)]

    results = method_results_gatherer(handles, 'execute', command, stdin=stdin,
            kwargs={'extra_arguments':extra_arguments})
    return results


def get_argparse_args(args=None):
    """
    Get the arguments passed to this script when it was run.

    @param args: A list of arguments passed in the console.
    @type args: list

    @returns: A tuple containing (args, command, extra_args)
    @rtype: tuple
    """
    if sys.version_info[:2] == (2, 7):
        from _info import __version__, __long_description__
    else:
        from sshm._info import __version__, __long_description__
    import argparse

    p = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=__long_description__)
    p.add_argument('servers')
    p.add_argument('command')
    args, extra_args = p.parse_known_args(args=args)
    return (args, args.command, extra_args)


def main():
    """
    Run SSHM using console provided arguments.

    This should only be run using a console!
    """
    import select
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
                result['instance'].uri,
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

