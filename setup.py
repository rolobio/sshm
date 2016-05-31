from setuptools import setup
from sshm._info import __version__, __long_description__
from sys import version_info

config = {
    'name':'sshm',
    'version':__version__,
    'author':'rolobio',
    'author_email':'rolobio+sshm@rolobio.com',
    'description':'SSH into multiple hosts.',
    'license':'GNU GPL',
    'keywords':'ssh multiple',
    'url':'https://github.com/rolobio/sshm',
    'packages':[
        'sshm',
        ],
    'long_description':__long_description__,
    'install_requires': [
        'pyzmq',
        ],
    'classifiers':[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)"
        ],
    'test_suite':'sshm.test.suite',
    'entry_points':{
        'console_scripts': [
            'sshm = sshm.main:main'
            ]
        },
    }

if version_info.major != 3 and version_info.minor != 2:
    # Only require netaddr when version is not 3.2, as its not supported
    # under 3.2
    config['install_requires'].append('netaddr')

setup(**config)

