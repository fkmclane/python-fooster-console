#!/usr/bin/env python3
import os
import re

from setuptools import setup, find_packages


name = None
version = None


def find(haystack, *needles):
    regexes = [(index, re.compile(r'^{}\s*=\s*[\'"]([^\'"]*)[\'"]$'.format(needle))) for index, needle in enumerate(needles)]
    values = ['' for needle in needles]

    for line in haystack:
        if len(regexes) == 0:
            break

        for rindex, (vindex, regex) in enumerate(regexes):
            match = regex.match(line)
            if match:
                values[vindex] = match.groups()[0]
                del regexes[rindex]
                break

    return values


with open(os.path.join(os.path.dirname(__file__), 'fooster', 'console', '__init__.py'), 'r') as console:
    name, version = find(console, 'name', 'version')


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as rfile:
    readme = rfile.read()


setup(
    name=name,
    version=version,
    description='todo',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/fkmclane/python-fooster-console',
    author='Foster McLane',
    author_email='fkmclane@gmail.com',
    install_requires=['paramiko'],
    packages=find_packages(),
    namespace_packages=['fooster'],
    classifiers=[
    ],
)