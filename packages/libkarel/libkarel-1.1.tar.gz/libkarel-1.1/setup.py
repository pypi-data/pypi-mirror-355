"""Setup tools for libkarel."""

import subprocess
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='libkarel',
    version=subprocess.check_output(['/usr/bin/git', 'describe', '--tags'],
                                    universal_newlines=True),
    author='omegaUp',
    author_email='lhchavez@omegaup.org',
    description='Utilities for validating karel.js test cases',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/omegaup/libkarel',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
