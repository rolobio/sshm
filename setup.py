import os
from setuptools import setup
from sshm._info import __version__, __long_description__

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
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)"
        ],
    'test_suite':'sshm.test.suite',
    'entry_points':{
        'console_scripts': [
            'sshm = sshm.sshm:main'
            ]
        },
    }

setup(**config)

