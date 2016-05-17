import os
import sys
import subprocess
import setuptools


class Command(setuptools.Command):

    requires = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._returncode = 0

    def finalize_options(self):
        pass

    def run(self):
        if type(self).requires:
            self.distribution.fetch_build_eggs(type(self).requires)
            self.run_command('egg_info')
            self.reinitialize_command('build_ext', inplace=1)
            self.run_command('build_ext')
        self.__call__()
        if self._returncode:
            sys.exit(self._returncode)

    def call(self, command):
        env = os.environ.copy()
        env['PYTHONPATH'] = ''.join(':' + x for x in sys.path)
        self.announce('Run command: {}'.format(command), level=2)
        try:
            subprocess.check_call(command.split(), env=env)
        except subprocess.CalledProcessError as error:
            self._returncode = 1
            message = 'Command failed with exit code {}'
            message = message.format(error.returncode)
            self.announce(message, level=2)


class TestCommand(Command):

    requires = ['pytest', 'pytest-cov']
    description = 'run tests and create a coverage report'
    user_options = [('args=', None, 'args to forward to pytest')]

    def initialize_options(self):
        self.args = ''

    def __call__(self):
        self.call('python3 -m pytest --cov=definitions test ' + self.args)


class LintCommand(Command):

    requires = ['pylint']
    description = 'run linters'
    user_options = [('args=', None, 'args to forward to pylint')]

    def initialize_options(self):
        self.args = ''

    def __call__(self):
        self.call('python3 -m pylint definitions ' + self.args)
        self.call('python3 -m pylint test ' + self.args)
        self.call('python3 -m pylint setup.py ' + self.args)


DESCRIPTION = 'Load and validate YAML definitions against a schema'

SETUP_REQUIRES = [
    'sphinx',
]

INSTALL_REQUIRES = [
    'PyYAML',
]

if __name__ == '__main__':
    setuptools.setup(
        name='definitions',
        version='0.2.0',
        description=DESCRIPTION,
        url='http://github.com/danijar/definitions',
        author='Danijar Hafner',
        author_email='mail@danijar.com',
        license='MIT',
        packages=['definitions'],
        setup_requires=SETUP_REQUIRES,
        install_requires=INSTALL_REQUIRES,
        tests_require=[],
        cmdclass={
            'test': TestCommand,
            'lint': LintCommand,
        },
    )

