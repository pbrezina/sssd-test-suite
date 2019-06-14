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

import textwrap

from commands.box import PruneBoxActor
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
            '--prune', action='store_true', dest='prune',
            help='Remove outdated boxes after update.'
        )

        parser.epilog = textwrap.dedent('''
        This command will run existing SSSD tests by executing
        sssd/contrib/test-suite/run-tests.sh.

        Existing 'client' machine will be destroyed and replaced with new one.
        Currently, all tests are run only on the client machine so it is the
        only guest that this command touches.
        ''')

    def run(self, args):
        tasks = self.tasklist('Tests')

        if args.update:
            tasks.add('Updating boxes', self.update, args)

        if args.prune:
            tasks.add('Removing outdated boxes', self.prune, args)

        tasks.add('Creating artifacts directory', self.create_artifacts_dir, args)
        tasks.add('Destroying current client', self.destroy, args)
        tasks.add('Starting client', self.up, args)
        tasks.add('Running tests', self.run_tests, args)
        tasks.add('Halting client', self.halt, args)
        tasks.run()

    def update(self, task, args):
        self.vagrant(args.config, 'box update', ['client'])

    def prune(self, task, args):
        self.call(PruneBoxActor(), args)

    def destroy(self, task, args):
        self.vagrant(args.config, 'destroy', ['client'])

    def up(self, task, args):
        self.vagrant(args.config, 'up', ['client'],
            env={
                'SSSD_TEST_SUITE_RSYNC': '{}:/shared/sssd'.format(args.sssd),
                'SSSD_TEST_SUITE_SSHFS': '{}:/shared/artifacts'.format(args.artifacts)
            },
            clear_env=True
        )

    def halt(self, task, args):
        self.vagrant(args.config, 'halt', ['client'])

    def create_artifacts_dir(self, task, args):
        self.shell(['mkdir', '-p', args.artifacts])

    def run_tests(self, task, args):
        self.vagrant(
            args.config, 'ssh', ['client'],
            ['/shared/sssd/contrib/test-suite/run-tests.sh']
        )


Commands = CommandList([
    Command('run', 'Run SSSD tests', RunTestsActor),
])
