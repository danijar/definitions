import os
import sys
import subprocess
import setuptools
from setuptools.command.test import test


class TestCommand(test):

    description = 'run tests, linters and create a coverage report'
    user_options = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.returncode = 0

    def finalize_options(self):
        super().finalize_options()
        # New setuptools don't need this anymore, thus the try block.
        try:
            # pylint: disable=attribute-defined-outside-init
            self.test_args = []
            self.test_suite = 'True'
        except AttributeError:
            pass

    def run_tests(self):
        self._call('python3 -m pytest --cov=definitions test')
        self._call('python3 -m pylint definitions')
        self._call('python3 -m pylint test')
        self._call('python3 -m pylint setup.py')
        self._check()

    def _call(self, command):
        env = os.environ.copy()
        env['PYTHONPATH'] = ''.join(':' + x for x in sys.path)
        print('Run command', command)
        try:
            subprocess.check_call(command.split(), env=env)
        except subprocess.CalledProcessError as error:
            print('Command failed with exit code', error.returncode)
            self.returncode = 1

    def _check(self):
        if self.returncode:
            sys.exit(self.returncode)


DESCRIPTION = 'Load and validate YAML definitions against a schema'

SETUP_REQUIRES = [
    'sphinx',
]

INSTALL_REQUIRES = [
    'PyYAML',
]

TESTS_REQUIRE = [
    'pytest',
    'pytest-cov',
    'pylint',
]


if __name__ == '__main__':
    setuptools.setup(
        name='definitions',
        version='0.1.0',
        description=DESCRIPTION,
        url='http://github.com/danijar/definitions',
        author='Danijar Hafner',
        author_email='mail@danijar.com',
        license='MIT',
        packages=['definitions'],
        setup_requires=SETUP_REQUIRES,
        install_requires=INSTALL_REQUIRES,
        tests_require=TESTS_REQUIRE,
        cmdclass={'test': TestCommand},
    )

