#! /usr/bin/env python3

# This is the official version of sshm
__version__ = '2.1.2'

__long_description__ = '''
    SSH Multi v%s. SSH into multiple machines at once.

    Examples:

        Get a count of processes on each server:

             $ sshm example1.com,example2.com,example3.com,mail[01-05].example.com,host[01-25].org "ps aux | wc -l"

        Check if postfix is running on mail servers:

             $ sshm 192.168.0.1-5 "postfix status"

        Verify which servers are accepting SSH connections:

             $ sshm example[1-5,8].com "exit"

        Copy a file to several servers (may not work for larger files):

             $ cat some_file | sshm example[1-5].com "cat > some_file"

        Specify a per-host port:

             $ sshm example1.com:123,example2.com,example4.com:78 "exit"

        Specify multiple groups of servers, the last positional argument is assumed to be the command.

            $ sshm 192.168.0.1-20 example.com,mail[03-5].example.com "uptime"

        Format the command per-host:

             $ sshm example[1-3].com "echo {fqdn}"

             Outputs:
                  sshm: example1.com(0): example1.com
                  sshm: example2.com(0): example2.com
                  sshm: example3.com(0): example3.com

             Possible formatting variables:
                  uri, fqdn, subdomain, num

        Quiet SSH's error output (-q is passed to the SSH command):

             $ sshm -u example.com "echo {subdomain}"

             executes:
                  (ssh -q example.com echo example)


        Any arguments not recognized by SSHM will be passed to ssh:

            $ ssh example.com "ls" -o StrictHostKeyChecking=no

        Attempt to get hostnames of the entire 10.0.0.0 subnet, do not store keys found, do not ask about keys found, do not prompt for password, timeout connection after 1 second, tell ssh to not display any error output. This command will take several days, and is not secure because all keys are ignored:

            $ sshm -q 10.0-255.0-255.0-255 "hostname" -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -oBatchMode=yes -oConnectTimeout=1
    ''' % (__version__)

