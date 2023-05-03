from setuptools import setup, find_packages
from pyrsmi._version import __version__

from os import path
from io import open


cwd = path.abspath(path.dirname(__file__))

with open(path.join(cwd, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyrsmi',
    version=__version__,
    description='Python Bindings for System Management Library for AMD GPUs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['rocm', 'smi', 'amd', 'system management'],
    author='AMD Author',
    python_requires='>=3.6',
    url='http://www.amd.com',
    license='BSD',
    packages=find_packages(exclude=['notebooks', 'docs', 'tests']),
    package_data={'pyrsmi': ['README.md']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware',
        'Topic :: System :: Systems Administration',
    ],
)
