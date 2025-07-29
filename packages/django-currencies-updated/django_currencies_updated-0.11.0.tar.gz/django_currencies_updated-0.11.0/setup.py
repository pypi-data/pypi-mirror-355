#!/usr/bin/env python

import os
import re
import sys
import codecs
import subprocess

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class TestRunner(TestCommand):
    user_options = []

    def run(self):
        exe = ['coverage', 'run', '--source=currencies']
        try:
            import coverage
        except ImportError:
            exe = [sys.executable]
        raise SystemExit(subprocess.call(exe + ['runtests.py']))


# When creating the sdist, make sure the django.mo file also exists:
if 'sdist' in sys.argv or 'develop' in sys.argv:
    os.chdir('currencies')
    try:
        from django.core import management
        management.call_command('compilemessages', stdout=sys.stderr, verbosity=1)
    except ImportError:
        if 'sdist' in sys.argv:
            raise
    finally:
        os.chdir('..')


def read(*parts):
    file_path = os.path.join(os.path.dirname(__file__), *parts)
    return codecs.open(file_path, encoding='utf-8').read()


def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return str(version_match.group(1))
    raise RuntimeError("Unable to find version string.")

setup(
    name='django-currencies-updated',
    version=find_version('currencies', '__init__.py'),

    install_requires=[
        'django>=3.1',
        'requests>=2.14.2',
        'beautifulsoup4',
    ],

    description='Adds support for multiple currencies as a Django application.',
    long_description_content_type='text/x-rst',
    long_description=read('README.rst'),

    author='Panos Laganakos',
    author_email='panos.laganakos@gmail.com',

    url='https://github.com/pkshahid/django-currencies',
    download_url='https://github.com/pkshahid/django-currencies/zipball/master',

    packages=find_packages(exclude=('example*', '*.tests*')),
    include_package_data=True,

# Not used when running python setup.py develop or test? See .travis.yml
    # tests_require=[
    #     'httpretty',    # for openexchangerates client
    #     'coverage',     # for code coverage report output
    #     'codecov',      # for codecov.io
    # ],
    # cmdclass={
    #     'test': TestRunner,
    # },

    zip_safe=False,
    license='BSD-3-Clause',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
