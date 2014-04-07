#! /usr/bin/env python3
import re
import subprocess
import sys
import threading
import zmq
from traceback import format_exc

__all__ = ['sshm']


# This is used to check if the target contains any alpha characters.
_alpha = re.compile(r'[a-zA-Z]')

def is_url(target):
    return bool(_alpha.search(target))


def target_expansion(input_str):
    """
    Expand a list of targets into invividual URLs/IPs and their respective
    ports. Preserve any zero-padding the range may contain.
    """


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

def ssh(thread_num, context, url, port, command, extra_arguments, stdin=None):
    """
    Create an SSH connection to 'url' on port 'port'.  Execute 'command' and
    pass any stdin to this ssh session.  Return the results via ZMQ (SINK_URL).

    @param context: Create all ZMQ sockets using this context.
    @type context: zmq.Context
    @param url: SSH to this url
    @type url: str

    @param port: destination's port
    @type port: str

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
            'url':url,
            'port':port,
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
        if port:
            cmd.extend([url, '-p', port, command])
        else:
            cmd.extend([url, command])

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
    for uri in target_expansion(servers):
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



