# -*- coding: utf-8 -*-
#
#    Authors:
#        Pavel Březina <pbrezina@redhat.com>
#
#    Copyright (C) 2019 Red Hat
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import tempfile
import textwrap
import yaml

from commands.box import PruneBoxActor
from commands.vagrant import VagrantCommandActor
from lib.command import CommandList, Command
from util.actor import TestSuiteActor


class RunTestsActor(TestSuiteActor):
    def setup_parser(self, parser):
        parser.add_argument(
            '--sssd', action='store', type=str, dest='sssd',
            help='Path to SSSD source directory.',
            required=True
        )

        parser.add_argument(
            '--artifacts', action='store', type=str, dest='artifacts',
            help='Path to directory where tests artifacts will be stored.',
            required=True,
        )

        parser.add_argument(
            '--update', action='store_true', dest='update',
            help='Update current boxes before running the tests.'
        )

        parser.add_argument(
            '--suite', action='store', type=str, dest='suite',
            help='Path to test suite yaml configuration.',
            required=False
        )

        parser.add_argument(
            '--prune', action='store_true', dest='prune',
            help='Remove outdated boxes after update.'
        )

        parser.epilog = textwrap.dedent('''
        This command will execute tests described in yaml configuration file.
        This file can be specified with --suite parameter. If not set,
        $sssd/contrib/test-suite/test-suite.yml is used.
        ''')

    def run(self, args):
        suite = self.load_test_suite(args)

        prepare = self.tasklist('Preparation')
        prepare.add('Creating artifacts directory', self.create_artifacts_dir, args)
        if args.update:
            prepare.add('Updating boxes', self.update, suite, args)
        if args.prune:
            prepare.add('Removing outdated boxes', self.prune, args)
        prepare.run()

        testcases = self.tasklist('Test Case')
        for testcase in suite:
            testcases.add(testcase['name'], self.test_case, testcase, args)
        testcases.run()

    def load_test_suite(self, args):
        suite = args.suite if args.suite else '{}/contrib/test-suite/test-suite.yml'.format(args.sssd)
        with open(suite) as f:
            return yaml.safe_load(f)
    
    def update(self, task, suite, args):
        machines = set()
        for case in suite:
            machines.update(case.get('machines', []))
        
        machines = list(machines)
        self.call(VagrantCommandActor('box update'), config=args.config, sequence=False, guests=machines)

    def prune(self, task, args):
        self.call(PruneBoxActor(), config=args.config)

    def create_artifacts_dir(self, task, args):
        self.shell(['mkdir', '-p', args.artifacts])

    def test_case(self, task, testcase, args):
        machines = testcase['machines']

        tasks = self.tasklist('Test Case: {}'.format(testcase['name']))
        tasks.add('Destroying current guests: {}'.format(machines), self.destroy, machines, args)
        tasks.add('Starting up guests: {}'.format(machines), self.up, machines, args)
        for test in testcase.get('tasks', []):
            tasks.add(test.get('name', ''), self.test, test, args)
        tasks.add('Halting machines', self.halt, machines, args)
        tasks.run()
    
    def destroy(self, task, machines, args):
        return
        self.call(VagrantCommandActor('destroy'), config=args.config, sequence=False, guests=machines)

    def up(self, task, machines, args):
        return
        for machine in machines:
            self.vagrant(args.config, 'up', [machine],
                env={
                    'SSSD_TEST_SUITE_RSYNC': '{}:/shared/sssd'.format(args.sssd),
                    'SSSD_TEST_SUITE_SSHFS': '{}:/shared/artifacts'.format(args.artifacts)
                },
                clear_env=True
            )

    def test(self, task, test, args):
            try:
                with open('{}/.suite-command'.format(self.root_dir), 'w') as f:
                    
            self.vagrant(
                    args.config, 'ssh', [machine],
                    ['echo', command, '>', '.suite.run.sh']
                )
        
        upload_command(test['machine'], test['script'])
        import sys
        sys.exit(0)
            
        try:
            if 'directory' in test:
                command = 'cd {} && {}'.format(test['directory'], test['script'])
            else:
                command = test['script']
            
            self.vagrant(
                args.config, 'ssh', [test['machine']],
                ['bash', '-c', command]
            )
        finally:
            command = ''
            for artifact in test.get('artifacts', []):
                command += 'cp {} /shared/artifacts ; '.format(artifact)
            
            if command:
                self.vagrant(
                    args.config, 'ssh', [test['machine']],
                    ['bash', '-c', command]
                )

    def halt(self, task, machines, args):
        self.call(VagrantCommandActor('halt'), config=args.config, sequence=False, guests=machines)

    def run_command(self, machine, directory, command):
        with tempfile.TemporaryFile() as f:
            if directory:
                f.write('cd {} || exit 1\n\n'.format(directory))

            f.write(command)
            self.shell('scp -i {}/.vagrant/{}/client/libvirt/private_key fedora@')

Commands = CommandList([
    Command('run', 'Run SSSD tests', RunTestsActor),
])
