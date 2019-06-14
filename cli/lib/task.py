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

import datetime
import sys

from .colors import format_colors


class Task(object):
    def __init__(self, name, handler, *args, **kwargs):
        self.tasklist = None
        self.name = name
        self.handler = handler
        self.args = args
        self.kwargs = kwargs

    def run(self, tasklist):
        self.tasklist = tasklist
        self.handler(self, *self.args, **self.kwargs)

    def message(self, message, **kwargs):
        self.tasklist.message(message, **kwargs)

    def error(self, message, **kwargs):
        if 'file' not in kwargs:
            kwargs['file'] = sys.stderr

        self.message(message, **kwargs)

    def step(self, description, group=None, indent=1, **kwargs):
        msg = '  ' * indent
        msg += '[{}] '.format(group) if group is not None else ''
        msg += str(description)

        self.message(msg, **kwargs)


class TaskList(object):
    def __init__(self, runner, name=None, tasks=[]):
        self.runner = runner
        self.name = name
        self.tasks = tasks

    def add(self, name, handler, *args, **kwargs):
        self.tasks.append(Task(name, handler, *args, **kwargs))

    def add_list(self, tasks):
        self.tasks += tasks

    def message(self, message, **kwargs):
        prefix = '' if self.name is None else '[{}] '.format(self.name)
        self.runner.message('{}{}'.format(prefix, message), **kwargs)

    def error(self, message, **kwargs):
        if 'file' not in kwargs:
            kwargs['file'] = sys.stderr

        self.message(message, **kwargs)

    def run(self):
        total = len(self.tasks)
        start = datetime.datetime.now()
        try:
            for idx, task in enumerate(self.tasks, start=1):
                self.message('[{}/{}] {}'.format(idx, total, task.name))
                task.run(self)
        except Exception as e:
            self.message('Finished with error {c-r}{cls}{s-r}: {message}'.format(
                cls=e.__class__.__name__,
                message=str(e),
                **format_colors()))
            raise

        end = datetime.datetime.now()

        hours, remainder = divmod((end - start).total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.message('Finished in {:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds)))
