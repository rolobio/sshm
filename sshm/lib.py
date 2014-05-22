#! /usr/bin/env python3
import re
import subprocess
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
invalid_uris = ValueError('Invalid URIs provided!')

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
        raise invalid_uris

    for uri in uris:
        user, prefix, range_str, suffix, ip_addr, port = uri

        if (prefix or suffix) and range_str:
            # Expand the URL
            i = product([prefix,], expand_ranges(range_str), [suffix,])
            i = [''.join(iter(j)) for j in i]
            new_uris.extend([create_uri(user, k, port) for k in i])
        elif ip_addr:
            # Check the length of this IP address
            if ip_addr.count('.') != 3:
                raise invalid_uris

            if '-' in ip_addr or ',' in ip_addr:
                # Expand any ranges in the octets
                x = [expand_ranges(i) for i in ip_addr.split('.')]
                # Create all products for each expanded octet
                j = product(x[0], x[1], x[2], x[3])
                # Join the octets back together with dots
                l = ['.'.join(iter(k)) for k in j]
                # Extend new_uris with the new URIs, conver them to a URI
                new_uris.extend([create_uri(user, i, port) for i in l])
            else:
                # No expansion necessary for IP
                new_uris.append(create_uri(user, ip_addr, port))
        else:
            # No expansion necessary for URL
            new_uris.append(create_uri(user, prefix+suffix, port))

    # Some targets must be specified
    if not new_uris:
        raise invalid_uris

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
STDIN_URL = 'inproc://stdin'

def ssh(thread_num, context, uri, command, extra_arguments, if_stdin=False):
    """
    Create an SSH connection to 'uri'.  Execute 'command' and
    pass any stdin to this ssh session.  Return the results via ZMQ (SINK_URL).

    @param context: Create all ZMQ sockets using this context.
    @type context: zmq.Context

    @param uri: user@example.com:22
    @type uri: str

    @param commmand: Execute this command on 'uri'.
    @type command: str

    @param extra_arguments: Pass these extra arguments to the ssh call.
    @type extra_arguments: list

    @param if_stdin: If this is True, this function will request stdin and
        write it to proc's stdin.
    @type if_stdin: bool

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
    # Get stdin
    stdin_sock = context.socket(zmq.REQ)
    stdin_sock.connect(STDIN_URL)

    try:
        cmd = ['ssh',]
        # Add extra arguments after ssh, but before the uri and command
        cmd.extend(extra_arguments or [])
        # Only change the port at the user's request.  Otherwise, use SSH's
        # default port.
        try:
            user_url, port = uri.split(':')
            cmd.extend([user_url, '-p', port, command])
        except ValueError:
            # No port provided
            cmd.extend([uri, command])

        # Run the command, return its results
        proc = popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,)

        # Write stdin to the PIPE until it is empty
        if if_stdin:
            while True:
                stdin_sock.send_pyobj(thread_num)
                chunk = stdin_sock.recv_pyobj()
                # If the chunk is None, the stdin is empty
                if chunk == None:
                    break
                # Continually attempt to send the chunk while the process is alive
                while proc.poll() == None:
                    try:
                        proc.stdin.write(chunk)
                        # successfully sent the chunk, get the next one
                        break
                    except IOError: # pragma: no cover not a predictable error
                        # Temporary error, attempt to send the chunk again
                        pass

        # Get the output
        stdout, stderr = proc.communicate()
        # Close stdin now that the process has ended
        proc.stdin.close()
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


CHUNK_SIZE = 65536

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
    # Used to send stdin to workers
    stdin_sock = context.socket(zmq.REP)
    stdin_sock.bind(STDIN_URL)

    # Python 3+ compatibility
    if 'buffer' in dir(stdin): # pragma: no cover version specific
        stdin = stdin.buffer

    # Start each SSH connection in it's own thread
    threads = []
    thread_num = 0
    # Only tell the thread to get stdin if there is some.
    if_stdin = True if stdin else False
    for uri in uri_expansion(servers):
        thread = threading.Thread(target=ssh, args=(thread_num, context, uri,
            command, extra_arguments, if_stdin))
        thread.start()
        threads.append(thread)
        thread_num += 1

    poller = zmq.Poller()
    poller.register(sink, zmq.POLLIN)
    poller.register(stdin_sock, zmq.POLLIN)

    # Report any results that have been returned and send STDIN in chunks
    # as fast as the threads can receive it.
    completed_threads = 0
    stdin_queue = dict(zip(range(len(threads)), [1 for i in range(len(threads))]))
    stdin_chunks = {}
    chunk_count = 1
    while completed_threads != len(threads):
        socks = dict(poller.poll())
        if socks.get(sink) == zmq.POLLIN:
            # A thread has finished, yield the results
            results = sink.recv_pyobj()
            completed_threads += 1
            yield results
            threads[results['thread_num']].join()
        elif socks.get(stdin_sock) == zmq.POLLIN:
            # A thread requests it's stdin, give it it's next chunk.
            thread_num = stdin_sock.recv_pyobj()
            # Read the next chunk to memory if it hasn't been read in yet
            if stdin_queue[thread_num] not in stdin_chunks:
                chunk = stdin.read(CHUNK_SIZE)
                if len(chunk) == 0:
                    chunk = None
                stdin_chunks[chunk_count] = chunk
                chunk_count += 1

            # Send their current chunk
            chunk = stdin_chunks[stdin_queue[thread_num]]
            stdin_sock.send_pyobj(chunk)
            # Set the next chunk
            stdin_queue[thread_num] += 1

            # Delete old chunks if they are unused
            min_needed = min([stdin_queue[i] for i in stdin_queue])
            min_in_memory = min(stdin_chunks)
            if min_needed > min_in_memory:
                del stdin_chunks[min_in_memory]

    # Cleanup
    sink.close()
    stdin_sock.close()
    context.term()



