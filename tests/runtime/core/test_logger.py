# -*- coding: utf-8 -*-
import logging
import sys

from support import RuntimeTest


class LoggerTests(RuntimeTest):
    def test_retained_filter_survives_cleared_module_globals(self):
        module = self.load('logger')
        retained = module.LocationFilter()
        try:
            raise ValueError('failure')
        except ValueError:
            record = logging.LogRecord('Driftkings.Reload', logging.ERROR,
                                       'example.py', 1, 'Failed', (), sys.exc_info())
        saved = (module.NAMESPACE, module.logging, module.os)
        try:
            module.NAMESPACE = module.logging = module.os = None
            self.assertTrue(retained.filter(record))
            self.assertIn('[ERROR][Driftkings][Reload] test_logger.py line ', record.getMessage())
        finally:
            module.NAMESPACE, module.logging, module.os = saved

    def test_names_share_the_existing_client_logger(self):
        factory = self.load('logger').get_logger
        expected = logging.getLogger('Driftkings.Settings')
        handlers = list(expected.handlers)
        level, propagate = expected.level, expected.propagate
        self.assertIs(factory('Settings'), expected)
        self.assertIs(factory('Driftkings.Settings'), expected)
        self.assertIs(factory(), logging.getLogger('Driftkings'))
        self.assertEqual(expected.handlers, handlers)
        self.assertEqual((expected.level, expected.propagate), (level, propagate))
        self.assertEqual(sum(bool(getattr(item, 'driftkings_location', False))
                             for item in expected.filters), 1)

    def test_exception_keeps_lazy_arguments_and_traceback(self):
        logger = self.load('logger').get_logger('tests.exceptions')
        records = []
        class Handler(logging.Handler):
            def emit(self, record):
                records.append(record)
        handler = Handler()
        old_level, old_propagate = logger.level, logger.propagate
        self.addCleanup(logger.setLevel, old_level)
        self.addCleanup(setattr, logger, 'propagate', old_propagate)
        self.addCleanup(logger.removeHandler, handler)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        try:
            failure_line = sys._getframe().f_lineno + 1
            raise ValueError('failure')
        except ValueError:
            logger.exception('Failed: %s', 'operation')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].getMessage(),
                         '[ERROR][Driftkings][tests.exceptions] test_logger.py line %s: Failed: operation' % failure_line)
        self.assertEqual(records[0].args, ('operation',))
        self.assertIs(records[0].exc_info[0], ValueError)

    def test_plain_error_location_and_other_levels(self):
        logger = self.load('logger').get_logger('tests.location')
        record = logging.LogRecord(logger.name, logging.ERROR, 'example.py', 17,
                                   'Failure: %s', ('details',), None)
        logger.filter(record)
        logger.filter(record)
        self.assertEqual(record.getMessage(),
                         '[ERROR][Driftkings][tests.location] example.py line 17: Failure: details')
        info = logging.LogRecord(logger.name, logging.INFO, 'example.py', 18,
                                 'Loaded %s', ('module',), None)
        logger.filter(info)
        self.assertEqual(info.getMessage(), '[INFO][Driftkings][tests.location] Loaded module')

    def test_all_standard_levels_use_the_same_format(self):
        logger = self.load('logger').get_logger('tests.levels')
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            record = logging.LogRecord(logger.name, level, 'module.py', 42,
                                       'Message %s', ('details',), None)
            logger.filter(record)
            location = ' module.py line 42:' if level >= logging.WARNING else ''
            self.assertEqual(record.getMessage(),
                             '[%s][Driftkings][tests.levels]%s Message details' % (logging.getLevelName(level), location))
