# -*- coding: utf-8 -*-
"""Run portable runtime tests on Python 2.7/3, and build tests on Python 3."""
from __future__ import print_function
import argparse
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GROUPS = ('core', 'settings', 'battle', 'lobby', 'integration')


def collect(suite, group=None):
    if suite in ('all', 'build', 'artifacts') and sys.version_info[0] < 3:
        raise ValueError('Build tooling tests require Python 3; use --suite runtime on Python 2.7')
    paths = []
    if suite in ('all', 'runtime'):
        paths.extend(os.path.join(HERE, 'runtime', name) for name in ([group] if group else GROUPS))
    if suite in ('all', 'build'):
        paths.append(os.path.join(HERE, 'build'))
    if suite == 'artifacts':
        paths.append(os.path.join(HERE, 'artifacts'))
    for path in [ROOT, HERE] + paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    result = unittest.TestSuite()
    for path in paths:
        found = unittest.TestLoader().discover(path, pattern='test_*.py')
        if not found.countTestCases():
            raise ValueError('No tests discovered in ' + path)
        result.addTests(found)
    return result


def identifiers(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for name in identifiers(item):
                yield name
        else:
            yield item.id()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('runtime', 'build', 'artifacts', 'all'), default='runtime')
    parser.add_argument('--group', choices=GROUPS)
    parser.add_argument('--wotmod', help='Existing compiled WOTMOD, required for --suite artifacts')
    parser.add_argument('--list', action='store_true', help='Print discovered test IDs without running tests')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if args.group and args.suite != 'runtime':
        parser.error('--group requires --suite runtime')
    if args.suite == 'artifacts':
        if not args.wotmod or not os.path.isfile(args.wotmod):
            parser.error('--suite artifacts requires --wotmod pointing to an existing compiled package')
        os.environ['DK_TEST_WOTMOD'] = os.path.abspath(args.wotmod)
    elif args.wotmod:
        parser.error('--wotmod requires --suite artifacts')
    try:
        suite = collect(args.suite, args.group)
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        print(json.dumps(sorted(identifiers(suite)), indent=2))
        return
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
