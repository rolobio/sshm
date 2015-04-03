#! /usr/bin/env python3

# This is the official version of sshm
__version__ = '1.4.1'

__long_description__ = '''
    SSH Multi v%s. SSH into multiple machines at once.

    Examples:
        Get a count of processes on each server:
            sshm example1.com,example2.com,example3.com,mail[01-05].example.com,host[01-25].org "ps aux | wc -l"

        Check if postfix is running on mail servers:
            sshm mail[01-03].example.com "postfix status"

        Verify which servers are accepting SSH connections:
            sshm example[1-5].com "exit"

        Copy a file to several servers.  May not work for larger files.
            cat some_file | sshm example[1-5].com "cat > some_file"

        Specify a per-host port:
            sshm example1.com:123,example2.com,example4.com:78 "exit"

        Format the command per-host:
            sshm example[1-3].com "echo {fqdn}"

            Outputs:
                sshm: example1.com(0): example1.com
                sshm: example2.com(0): example2.com
                sshm: example3.com(0): example3.com

            Possible formatting variables:
                uri, fqdn, subdomain, num
    ''' % (__version__)

