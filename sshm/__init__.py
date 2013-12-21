import sysconfig

python_version = sysconfig.get_python_version()
if python_version == '2.7':
    from sshm import *
    from _info import *
elif python_version in ['3.2', '3.3']:
    from sshm.sshm import *
    from sshm._info import *

