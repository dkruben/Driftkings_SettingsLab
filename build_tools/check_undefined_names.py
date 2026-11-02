# -*- coding: utf-8 -*-
"""Fail when client sources use a name that is never defined or imported.

Python 2 only names (unicode, long, ...) and engine builtins are allowed.
Requires pyflakes (`pip install pyflakes`). Run: python build_tools/check_undefined_names.py
"""
import os
import sys

from pyflakes import api, messages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client')
ALLOWED = ('unicode', 'long', 'xrange', 'StandardError', 'basestring', 'reduce', 'unichr', 'file', 'cmp', 'raw_input')
SKIP_DIRS = ()


class Reporter(object):
    def __init__(self):
        self.problems = []

    def unexpectedError(self, filename, message):
        self.problems.append('%s: %s' % (filename, message))

    def syntaxError(self, filename, message, *args):
        # Python 2 only syntax cannot be parsed here; the Python 2.7 CI step covers it.
        pass

    def flake(self, message):
        if isinstance(message, messages.UndefinedName) and message.message_args[0] not in ALLOWED:
            self.problems.append('%s:%s: undefined name %r' % (message.filename, message.lineno,
                                                               message.message_args[0]))


def main():
    reporter = Reporter()
    for folder, dirs, names in os.walk(CLIENT):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in names:
            if name.endswith('.py'):
                path = os.path.join(folder, name)
                with open(path, 'rb') as source:
                    api.check(source.read().decode('utf-8'), path, reporter)
    for problem in sorted(reporter.problems):
        print(os.path.relpath(problem, ROOT) if os.path.isabs(problem) else problem)
    print('%d undefined name(s)' % len(reporter.problems))
    return 1 if reporter.problems else 0


if __name__ == '__main__':
    sys.exit(main())
