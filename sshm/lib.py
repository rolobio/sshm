#! /usr/bin/env python3
import io
import re
import subprocess
import sys
import tempfile
import threading
import zmq
from traceback import format_exc

__all__ = ['ssh', 'sshm']


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


def Popen(cmd, stdin, stdout, stderr):
    """
    Separating Popen call from ssh command for testing.
    """
    import subprocess
    proc = subprocess.Popen(cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,)
    return proc


def ssh(context, sink_url, requests_url,
        url, port, command, extra_arguments,
        ):
    """
    Create an SSH connection to 'url' on port 'port'.  Execute 'command' and
    pass any stdin to this ssh session.  Return the results via ZMQ (sink_url).

    @param context: Create all ZMQ sockets using this context.
    @type context: zmq.Context

    @param sink_url: The result will be sent to this ZMQ sink.
    @type sink_url: str

    @param url: SSH to this url
    @type url: str

    @param port: destination's port
    @type port: str

    @param commmand: Execute this command on 'url'.
    @type command: str

    @param extra_arguments: Pass these extra arguments to the ssh call.
    @type extra_arguments: list

    @returns: None
    """
    # This is the basic result that we send back
    result = {
            'url':url,
            'port':port,
            }

    # Send the results to this sink
    sink = context.socket(zmq.PUSH)
    sink.connect(sink_url)

    # Get stdin
    requests = context.socket(zmq.REQ)
    requests.connect(requests_url)
    requests.send_unicode('get stdin')
    stdin = requests.recv_pyobj()

    try:
        cmd = ['ssh',]
        # Add extra arguments after ssh, but before the uri and command
        cmd.extend(extra_arguments or [])
        # Only change the port at the user's request.  Otherwise, use SSH's
        # default port.
        if port:
            cmd.extend([url, '-p', port, command])
        else:
            cmd.extend([url, command])

        # Run the command, return its results
        proc = Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,)

        # Get the output
        stdout, stderr = proc.communicate(input=stdin)
        # Convert output into a usable format
        if 'decode' in dir(stdout):
            stdout = stdout.decode()
        if 'decode' in dir(stderr):
            stderr = stderr.decode()

        result.update({'return_code':proc.returncode,
                    'stdout':stdout,
                    'stderr':stderr,
                    # Nothing to result in traceback
                    'traceback':'',
                    }
                )
    except:
        # Oops, result the traceback
        result.update({
                'traceback':format_exc(),
                }
            )

    # Add the cmd to the result
    result.update({'cmd':cmd,})

    # Send the results!
    sink.send_pyobj(result)

    sink.close()
    requests.close()



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
    # Read in the contents of stdin
    if stdin:
        if sys.version_info[:1] <= (2, 7):
            stdin_contents = stdin.read()
        else:
            stdin_contents = stdin.buffer.read()
        stdin.close()
    else:
        stdin_contents = None

    context = zmq.Context()
    # The results of each ssh call is reported to this sink
    sink_url = 'inproc://sink'
    sink = context.socket(zmq.PULL)
    sink.bind(sink_url)
    # Requests for the contents of STDIN will come to this rep
    request_url = 'inproc://stdin'
    requests = context.socket(zmq.REP)
    requests.bind(request_url)

    # Start each SSH connection in it's own thread
    threads = []
    for url, port in expand_servers(servers):
        thread = threading.Thread(target=ssh,
                # Provide the arguments that ssh needs.
                args=(context, sink_url, request_url,
                    url, port, command, extra_arguments)
                )
        thread.start()
        threads.append(thread)

    # Listen for stdin requests and job results
    poller = zmq.Poller()
    poller.register(sink, zmq.POLLIN)
    poller.register(requests, zmq.POLLIN)

    # While any thread is active, respond to any requests.
    # If a thread sends a result, clean it up.
    completed_threads = 0
    while completed_threads != len(threads):
        sockets = dict(poller.poll())
        if (sink in sockets) and (sockets[sink] == zmq.POLLIN):
            # Got a result in the sink!
            result = sink.recv_pyobj()
            completed_threads += 1
            yield result
        elif (requests in sockets) and (sockets[requests] == zmq.POLLIN):
            if requests.recv_unicode() == 'get stdin':
                # A thread requests the contents of STDIN, send it
                requests.send_pyobj(stdin_contents)

    # Cleanup threads
    for thread in threads:
        thread.join()

    sink.close()
    requests.close()
    context.term()


def get_argparse_args(args=None):
    """
    Get the arguments passed to this script when it was run.

    @param args: A list of arguments passed in the console.
    @type args: list

    @returns: A tuple containing (args, command, extra_args)
    @rtype: tuple
    """
    try:
        from _info import __version__, __long_description__
    except ImportError:
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


