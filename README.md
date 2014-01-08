sshm
====
[![Build Status](https://travis-ci.org/rolobio/sshm.png?branch=master)](https://travis-ci.org/rolobio/sshm)

SSH Multiple. SSH into multiple machines and execute a single command.

# Installation
Installation is simple:

    $ python setup.py install

You can now import directly from sshm:

```python
from sshm.sshm import sshm
sshm('example[5,8].com', 'ls /dev/sd*')
```
or run it on your console:

    $ sshm example[01-40].com "exit"


# Examples
Get a count of processes on each server:

     $ sshm example1.com,example2.com,example3.com,mail[01-05].example.com,host[01-25].org "ps aux | wc -l"

Check if postfix is running on mail servers:

     $ sshm mail[01-03].example.com "postfix status"

Verify which servers are accepting SSH connections:

     $ sshm example[1-5].com "exit"

Copy a file to several servers (may not work for larger files):

     $ cat some_file | sshm example[1-5].com "cat > some_file"

Specify a per-host port:

     $ sshm example1.com:123,example2.com,example4.com:78 "exit"


