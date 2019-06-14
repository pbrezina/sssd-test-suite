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

import os

from lib.command import Actor
from lib.shell import Shell


class TestSuiteActor(Actor):
    LinuxGuests = ['ipa', 'ldap', 'client']
    WindowsGuests = ['ad', 'ad-child']
    AllGuests = WindowsGuests + LinuxGuests

    def __init__(self):
        super().__init__()
        self.root_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/../..')
        self.pool_dir = self.root_dir + '/pool'
        self.default_config = os.environ.get(
            'SSSD_TEST_SUITE_CONFIG',
            self.root_dir + '/config.json'
        )

    def ansible(self, playbook, unattended, limit=[], argv=[], **kwargs):
        env = {
            'ANSIBLE_SSH_ARGS': '-o UserKnownHostsFile=/dev/null '
                                '-o IdentitiesOnly=yes '
                                '-o ControlMaster=auto '
                                '-o ControlPersist=60s '
                                '-o ServerAliveInterval=15',
            'ANSIBLE_HOST_KEY_CHECKING': 'false'
        }

        limit = ','.join(limit) if limit else 'all'

        if not unattended:
            argv.append('--ask-become-pass')

        args = [
            '--limit', limit,
            '--inventory-file', '{}/provision/inventory.yml'.format(self.root_dir),
            *argv,
            '{}/provision/{}'.format(self.root_dir, playbook)
        ]

        return Shell().run(['ansible-playbook'] + args, env=env, **kwargs)

    def vagrant(self, config, command, args=[], argv=[], env={}, **kwargs):
        env = env.copy()
        env.update({
            'VAGRANT_CWD': self.root_dir,
            'SSSD_TEST_SUITE_CONFIG': config if config else self.default_config
        })

        if argv:
            args += ['--'] + argv

        return Shell().run(
            ['vagrant'] + command.split(' ') + args,
            env=env, **kwargs
        )
