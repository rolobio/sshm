import sys

if sys.version_info[:1] <= (2, 7):
    from sshm import *
    from _info import *
else:
    # Python 3
    from sshm.sshm import *
    from sshm._info import *

