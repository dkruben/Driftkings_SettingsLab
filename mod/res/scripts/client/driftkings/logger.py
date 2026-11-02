# -*- coding: utf-8 -*-
"""Single logger factory; handlers and output remain owned by the game client."""
import logging
import os

NAMESPACE = 'Driftkings'


class LocationFilter(logging.Filter):
    """Add the source location to warnings and errors; the client's log already names the level and logger."""
    driftkings_location = True

    def __init__(self):
        logging.Filter.__init__(self)
        # Loggers retain their filters across module reloads. Python 2 clears
        # the old module globals, so keep everything needed by filter here.
        self._warning = logging.WARNING
        self._basename = os.path.basename

    def filter(self, record):
        if getattr(record, 'driftkings_formatted', False) or record.levelno < self._warning:
            return True
        filename = getattr(record, 'driftkings_filename', record.filename)
        lineno = getattr(record, 'driftkings_lineno', record.lineno)
        if record.exc_info and record.exc_info[2] is not None:
            frame = record.exc_info[2]
            while frame.tb_next is not None:
                frame = frame.tb_next
            filename = self._basename(frame.tb_frame.f_code.co_filename)
            lineno = frame.tb_lineno
        record.msg = '%s line %s: ' % (filename, lineno) + record.msg
        record.driftkings_formatted = True
        return True


def get_logger(name=NAMESPACE):
    """Accept a full channel, a short name or a module path within the Driftkings namespace."""
    # 'driftkings.core.x' becomes 'Driftkings.core.x', not 'Driftkings.driftkings.core.x'.
    if name.startswith('driftkings.'):
        name = name[len('driftkings.'):]
    if name != NAMESPACE and not name.startswith(NAMESPACE + '.'):
        name = NAMESPACE + '.' + name
    logger = logging.getLogger(name)
    if not any(getattr(item, 'driftkings_location', False) for item in logger.filters):
        logger.addFilter(LocationFilter())
    return logger
