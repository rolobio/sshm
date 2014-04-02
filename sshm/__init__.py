"""
This module can be used to ssh into multiple servers at once.

Example:
    from sshm import sshm

    for result in sshm('example[5,8].com', 'ps aux | wc -l'):
            print(result)

    {
        'traceback': '',
        'stdout': u'195\n',
        'url': 'example5.com',
        'cmd': ['ssh', 'example5.com','ps aux | wc -l'],
        'return_code': 0,
        'stderr': u'',
        'port': ''
        }
    {
        'traceback': '',
        'stdout': u'120\n',
        'url': 'example8.com',
        'cmd': ['ssh', 'example8.com', 'ps aux | wc -l'],
        'return_code': 0,
        'stderr': u'',
        'port': ''
        }
"""

