#! /usr/bin/env python3
import re
import subprocess
import sys
import threading
import zmq
from itertools import product
from traceback import format_exc

__all__ = ['sshm', 'uri_expansion']


# This is used to parse a range string
_match_ranges = re.compile(r'(?:(\d+)(?:,|$))|(?:(\d+-\d+))')

def expand_ranges(to_expand):
    """
    Convert a comma-seperated range of integers into a list. Keep any zero
    padding the numbers may have.

        Example: "1,4,07-10" to ['1', '4', '07', '08', '09', '10']

    @param to_expand: Expand this string into a list of integers.
    @type to_expand: str
    """
    nums = []
    for single, range_str in _match_ranges.findall(to_expand):
        if single:
            nums.append(single)
        if range_str:
            i, j = range_str.split('-')
            # Create a string that will pad the integer with its current amount
            # of zeroes.
            # Example: if i is '03' the string will be '%0.2d'
            padding = '%'+'0.%d' % len(i) +'d'
            for k in range(int(i), int(j)+1):
                nums.append(padding % k)
    return nums


def create_uri(user, target, port):
    """
    Create a valid URI from the provided parameters.
    """
    if user and port:
        return user+'@'+target+':'+port
    elif user:
        return user+'@'+target
    elif port:
        return target+':'+port
    else:
        return target


_parse_uri = re.compile(r'(?:(\w+)@)?(?:(?:([a-zA-Z][\w.]+)(?:\[([\d,-]+)\])?([\w.]+)?)|([\d,.-]+))(?::(\d+))?,?')
invalid_urls = ValueError('Invalid URIs provided!')

def uri_expansion(input_str):
    """
    Expand a list of uris into invividual URLs/IPs and their respective
    ports and usernames. Preserve any zero-padding the range may contain.

    @param input_str: The uris to expand
    @type input_str: str
    """
    new_uris = []
    try:
        uris = _parse_uri.findall(input_str)
    except TypeError:
        raise invalid_urls

    for uri in uris:
        user, prefix, range_str, suffix, ip_addr, port = uri

        if (prefix or suffix) and range_str:
            # Expand the URL
            products = [''.join([i,j,k]) for i, j, k in product([prefix,], expand_ranges(range_str), [suffix,])]
            new_uris.extend([create_uri(user, p, port) for p in products])
        elif ip_addr:
            # Check the length of this IP address
            if ip_addr.count('.') != 3:
                raise invalid_urls

            if '-' in ip_addr or ',' in ip_addr:
                eo = [expand_ranges(i) for i in ip_addr.split('.')]

                # Create all products for each octet, add these to the next
                # octet.
                products = ['.'.join([i,j,k,l]) for i,j,k,l in product(eo[0], eo[1], eo[2], eo[3])]
                # Extend new_uris with the new URIs
                new_uris.extend([create_uri(user, p, port) for p in products])
            else:
                # No expansion necessary for IP
                new_uris.append(create_uri(user, ip_addr, port))
        else:
            # No expansion necessary for URL
            new_uris.append(create_uri(user, prefix+suffix, port))

    # Some targets must be specified
    if not new_uris:
        raise invalid_urls

    return new_uris


def popen(cmd, stdin, stdout, stderr): # pragma: no cover
    """
    Separating Popen call from ssh command for testing.
    """
    proc = subprocess.Popen(cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,)
    return proc


# ZMQ urls used to connect sshm and ssh
SINK_URL = 'inproc://sink'

def ssh(thread_num, context, uri, command, extra_arguments, stdin=None):
    """
    Create an SSH connection to 'url' on port 'port'.  Execute 'command' and
    pass any stdin to this ssh session.  Return the results via ZMQ (SINK_URL).

    @param context: Create all ZMQ sockets using this context.
    @type context: zmq.Context

    @param url: user@example.com:22
    @type url: str

    @param commmand: Execute this command on 'url'.
    @type command: str

    @param extra_arguments: Pass these extra arguments to the ssh call.
    @type extra_arguments: list

    @param stdin: A memoryview object containing sshm's stdin.
    @type stdin: memory

    @returns: None
    """
    # This is the basic result that we send back
    result = {
            'thread_num':thread_num,
            'uri':uri,
            }

    # Send the results to this sink
    sink = context.socket(zmq.PUSH)
    sink.connect(SINK_URL)

    try:
        cmd = ['ssh',]
        # Add extra arguments after ssh, but before the uri and command
        cmd.extend(extra_arguments or [])
        # Only change the port at the user's request.  Otherwise, use SSH's
        # default port.
        try:
            url, port = uri.split(':')
            cmd.extend([url, '-p', port, command])
        except ValueError:
            # No port provided
            cmd.extend([uri, command])

        # Run the command, return its results
        proc = popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,)

        # Get the output
        stdout, stderr = proc.communicate(input=stdin)
        # Convert output into a usable format
        if 'decode' in dir(stdout): # pragma: no cover version specific
            stdout = stdout.decode()
        if 'decode' in dir(stderr): # pragma: no cover version specific
            stderr = stderr.decode()

        result.update({'return_code':proc.returncode,
                    'stdout':stdout,
                    'stderr':stderr,
                    }
                )
    except:
        # Oops, get the traceback
        result.update({
                'traceback':format_exc(),
                }
            )

    # Add the cmd to the result
    result.update({'cmd':cmd,})

    # Send the results!
    sink.send_pyobj(result)

    sink.close()



def sshm(servers, command, extra_arguments=None, stdin=None):
    """
    SSH into multiple servers and execute "command". Pass stdin to these ssh
    handles.

    This is a generator to facilitate using the results of each ssh command as
    they become available.

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
    context = zmq.Context()
    # The results of each ssh call is reported to this sink
    sink = context.socket(zmq.PULL)
    sink.bind(SINK_URL)

    if stdin:
        if sys.version_info[:1] <= (2, 7): # pragma: no cover version specific
            stdin_contents = stdin.read()
        else: # pragma: no cover version specific
            stdin_contents = stdin.buffer.read()
        stdin.close()
    else:
        # No stdin provided
        stdin_contents = bytes()

    # Start each SSH connection in it's own thread
    threads = []
    thread_num = 0
    for uri in uri_expansion(servers):
        stdin_mv = memoryview(stdin_contents)
        thread = threading.Thread(target=ssh,
                # Provide the arguments that ssh needs.
                args=(thread_num, context, uri, command, extra_arguments, stdin_mv)
                )
        thread.start()
        threads.append(thread)
        thread_num += 1

    # If a thread sends a result, clean it up.
    completed_threads = 0
    while completed_threads != len(threads):
        results = sink.recv_pyobj()
        completed_threads += 1
        yield results
        threads[results['thread_num']].join()

    # Cleanup
    sink.close()
    context.term()



