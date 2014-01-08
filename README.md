sshm
====
[![Build Status](https://travis-ci.org/rolobio/sshm.png?branch=master)](https://travis-ci.org/rolobio/sshm)
[![Version](https://pypip.in/v/sshm/badge.png)](https://pypi.python.org/pypi/sshm/)
[![Egg Status](https://pypip.in/egg/sshm/badge.png)](https://pypi.python.org/pypi/sshm/)
[![Downloads](https://pypip.in/d/sshm/badge.png?period=month)](https://pypi.python.org/pypi/sshm/)
[![License](https://pypip.in/license/sshm/badge.png)](https://gnu.org/licenses/gpl.html)

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


