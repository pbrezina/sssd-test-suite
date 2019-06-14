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

from lib.shell import ShellScriptError
from lib.actions import UniqueAppendAction
from lib.command import CommandList, Command
from util.actor import TestSuiteActor


class VagrantCommandActor(TestSuiteActor):
    def __init__(self, command):
        super().__init__()
        self.command = command

    def _may_continue_on_exception(self, err):
        """
        Some vagrant command return non-zero exit codes on sucessful runs.
        """
        allowed_codes = []
        if self.command == 'destroy':
            allowed_codes = [2]

        if err.returncode in allowed_codes:
            return

        raise

    def setup_parser(self, parser):
        parser.add_argument(
            'guests', nargs='*',
            choices=['all'] + self.AllGuests,
            action=UniqueAppendAction,
            default='all',
            help='Guest to run the command with. '
                 'Multiple guests can be set. (Default "all")'
        )

        parser.add_argument(
            '-s', '--sequence', action='store_true', dest='sequence',
            help='Run operation on guests in sequence (one by one)'
        )

    def run(self, args):
        guests = args.guests if 'all' not in args.guests else self.AllGuests
        guests.sort()

        if args.sequence:
            for guest in guests:
                try:
                    self.vagrant(args.config, self.command, [guest])
                except ShellScriptError as err:
                    self._may_continue_on_exception(err)
            return

        try:
            self.vagrant(args.config, self.command, guests)
        except ShellScriptError as err:
            self._may_continue_on_exception(err)


class VagrantExternalCommandActor(TestSuiteActor):
    def __init__(self, command, allowed_guests, example):
        super().__init__()
        self.command = command
        self.allowed_guest = allowed_guests
        self.example = example

    def setup_parser(self, parser):
        parser.add_argument(
            'guest',
            type=str,
            choices=self.allowed_guest
        )

        parser.epilog = textwrap.dedent('''
        All parameters placed after -- will be passed to {cmd} command.
        For example:
            sssd-test-suite {cmd} {example}
        ''').format(cmd=self.command, example=self.example)

    def run(self, args, argv):
        self.vagrant(args.config, self.command, [args.guest], argv)


Commands = CommandList([
    Command('status', 'Show current state of guest machines', VagrantCommandActor('status')),
    Command('up', 'Bring up guest machines', VagrantCommandActor('up')),
    Command('halt', 'Halt guest machines', VagrantCommandActor('halt')),
    Command('destroy', 'Destroy guest machines', VagrantCommandActor('destroy')),
    Command('reload', 'Restarts guest machines', VagrantCommandActor('reload')),
    Command('resume', 'Resume suspended guest machines', VagrantCommandActor('resume')),
    Command('suspend', 'Suspends guest machines', VagrantCommandActor('suspend')),
    Command('ssh', 'Open SSH to guest machine', VagrantExternalCommandActor(
        'ssh', TestSuiteActor.LinuxGuests, 'client -- echo Hello')
    ),
    Command('rdp', 'Open remote desktop to guest machine', VagrantExternalCommandActor(
        'rdp', TestSuiteActor.WindowsGuests, 'ad -- -g 90%')
    ),
])
