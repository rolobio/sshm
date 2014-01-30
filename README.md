# SSHM
## About
[![Build Status](https://travis-ci.org/rolobio/sshm.png?branch=master)](https://travis-ci.org/rolobio/sshm)
[![Version](https://pypip.in/v/sshm/badge.png)](https://pypi.python.org/pypi/sshm/)
[![Egg Status](https://pypip.in/egg/sshm/badge.png)](https://pypi.python.org/pypi/sshm/)
[![Downloads](https://pypip.in/d/sshm/badge.png?period=month)](https://pypi.python.org/pypi/sshm/)
[![License](https://pypip.in/license/sshm/badge.png)](https://gnu.org/licenses/gpl.html)

SSH Multiple. SSH into multiple machines and execute a single command. Each ssh
session will be executed at once in their own threads. Stdin will be copied to
each session.

## Installation
Manual installation is simple:

    $ python setup.py install

or, automatic installation:

    $ pip install sshm

## Examples
Import directly from sshm:

```python
from sshm import sshm

for result in sshm('example[5,8].com', 'ps aux | wc -l'):
    print(result)

{'traceback': '', 'stdout': u'195\n', 'url': 'example5.com', 'cmd': ['ssh', 'example5.com', 'ps aux | wc -l'], 'return_code': 0, 'stderr': u'', 'port': ''}
{'traceback': '', 'stdout': u'120\n', 'url': 'example8.com', 'cmd': ['ssh', 'example8.com', 'ps aux | wc -l'], 'return_code': 0, 'stderr': u'', 'port': ''}
```
or run it on your console:

    $ sshm example[01-40].com "exit"


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


