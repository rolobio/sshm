import sysconfig

python_version = sysconfig.get_python_version()
if python_version[0] == '2':
    from sshm import *
    from _info import *
elif python_version[0] == '3':
    from sshm.sshm import *
    from sshm._info import *

