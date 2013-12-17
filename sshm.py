#! /usr/bin/env python3
import argparse
import re
import subprocess
import sys
import tempfile
import threading
import zmq


DEFAULT_PORT = '22'

class SSHHandle(object):

    def __init__(self, uri, port):
        self.uri = uri
        self.port = port

    def execute(self, command, stdin=None):
        """
        Perform an SSH command, pass it this script's STDIN.

        @type uri: str
        @param uri: The URI used to connect to a sepecific server.

        @type command: str
        @param command: Execute this one the remote server.

        @type stdin: file
        @param stdin: Pass this file handle to the ssh connection. Will be seen as
            STDIN remotely.
        """
        proc = subprocess.Popen(
            ['ssh', '-o UserKnownHostsFile=~/.ssh/known_hosts',
                self.uri, '-p', self.port, command],
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr)

        if stdin:
            stdin.close()

        return stdout.decode()



class MethodResultsGatherer(object):

    def __init__(self, instances, method_name, args):
        """
        Execute the method named "method_name" on all instances with the arguements in args.

        @type instances: list
        @param instances: The instances whose methods will be executed.

        @type method_name: str
        @param method_name: Will be executed on each instance.

        @type args: tuple or list
        @param args: If args is a tuple, that tuple will be passed to each
            thread. If args is a list, that list will be popped into each
            thread in reverse order. (Start to end)
        """
        if type(args) == list:
            # There must be an argument tuple for each instance.
            assert len(args) == len(instances)
            # Reverse the list so the arguments will be popped in order for each
            # instance.
            args = args[::-1]

        # Create the ZMQ connection
        self.context = zmq.Context()
        self.url = 'inproc://method_results_gatherer'
        self.conn = self.context.socket(zmq.PULL)
        self.conn.bind(self.url)

        self.threads = []
        for instance in instances:
            if type(args) != list:
                thread = threading.Thread(target=self._wrapper, args=(instance, method_name, args))
            else:
                thread = threading.Thread(target=self._wrapper, args=(instance, method_name, args.pop()))
            thread.start()
            self.threads.append(thread)


    def _wrapper(self, instance, method_name, args):
        """
        I perform a method and report what the method returns.
        """
        conn = self.context.socket(zmq.PUSH)
        conn.connect(self.url)

        try:
            method = getattr(instance, method_name)
            if type(args) in [list, tuple]:
                stdout = method(*args)
            else:
                stdout = method(args)
            conn.send_pyobj((True, instance, stdout))
        except Exception as e:
            conn.send_pyobj((False, instance, e))
        finally:
            conn.close()


    def get_results(self):
        """
        Collect the results of the threads that were run. Each instance is in a
        tuple with it's results. The first object in the tuple is True if the
        method succeeded, False if an error occured.

        Return example:
            (
                (True, Instance01('example01.com'), 'some stuff'),
                (False, Instance02('example02.com'), 'other stuff'),
            )
        """
        results = []
        if not self.conn.closed:
            for ign in self.threads:
                success, instance, stdout = self.conn.recv_pyobj()
                results.append((success, instance, stdout))

            # All messages have been received, join all threads
            for thread in self.threads:
                thread.join()

            self.conn.close()
            self.context.term()

            return results
        else:
            raise Exception('Messages have already been collected!')



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
    uri = ''
    if user: uri += user+'@'
    uri += body
    uri += num
    uri += suffix
    return (uri, port or DEFAULT_PORT)


EXTRACT_URIS = re.compile(r'([@\w._:-]+(?:\[[\d,-]+\])?(?:[@\w._:-]+)?)(?:,|$)')
PARSE_URI = re.compile(r'(?:([\w._-]+)@)?(?:([\w._-]+)(?:\[([\d,-]+)\])?([\w._-]+)?)(?::([\d+]+))?$')
def expand_servers(server_list):
    """
    Create a URI string for each server in the list.

        Example: 'example[3-5].com' to
            ['example3.com', 'example4.com', 'example5.com']
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



def sshm(servers, command, stdin=None):
    """
    SSH into multiple servers and execute "command". Pass stdin to these ssh
    connections.
    """
    handles = [SSHHandle(*u) for u in expand_servers(servers)]

    if stdin:
        # STDIN is provided, make a copy of it for each machine
        stdin = stdin.read()
        fhs = []
        for ign in handles:
            fh = tempfile.NamedTemporaryFile('w')
            fh.write(stdin)
            fh.seek(0)
            fhs.append(fh)
        t = MethodResultsGatherer(handles, 'execute', [(command, fh) for fh in fhs])
    else:
        # No STDIN. We'll just execute the command.
        t = MethodResultsGatherer(handles, 'execute', command)
    return t.get_results()


def pad_output(message):
    """
    If a message contains multiple lines, preceed it with a newline.
    """
    if isinstance(message, Exception):
        return str(message)
    else:
        if '\n' in message:
            return '\n'+message
        return message



if __name__ == '__main__':
    import select
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
    SSH Multi. SSH into multiple machines at once.

    Examples:
        Get a count of processes on each server:
            ./sshm example1.com,example2.com,example3.com,mail[01-05].example.com,host[01-25].org "ps aux | wc -l"

        Check if postfix is running on mail servers:
            ./sshm mail[01-03].example.com "postfix status"

        Verify which servers are accepting SSH connections:
            ./sshm example[1-5].com "exit"

        Copy a file to several servers.  May not work for larger files.
            cat some_file | ./sshm example[1-5].com "cat > some_file"
    '''
    )
    p.add_argument('servers')
    p.add_argument('command', nargs='+')
    args = p.parse_args()

    command = ' '.join(args.command)

    # Only provided stdin if there is data
    r_list, w_list, x_list = select.select([sys.stdin], [], [], 0)
    if r_list:
        stdin = r_list[0]
    else:
        stdin = None

    failure = False
    results = sshm(args.servers, command, stdin)
    for success, handle, message in results:
        if success:
            # Success! Print it out as it is received
            print(handle.uri, pad_output(message))
        else:
            # Failure, we'll display these in a list at the end.
            failure = True
            print('Failure:', handle.uri, pad_output(message))

    # Exit with non-zero when there is a failure
    if failure:
        sys.exit(1)

