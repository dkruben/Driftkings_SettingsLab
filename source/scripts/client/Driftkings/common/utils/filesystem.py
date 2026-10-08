# -*- coding: utf-8 -*-
"""Small file helpers compatible with the client's Python 2 runtime."""
import os
import tempfile


def recoverFile(path):
    """Restore the previous file if the client stopped during publication."""
    from Driftkings.settings.store import recover_file
    recover_file(path)


def atomicWrite(path, data):
    """Replace a file only after its complete replacement has been written."""
    from Driftkings.settings.store import replace_file
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    descriptor, temporary = tempfile.mkstemp(prefix='.driftkings-', dir=directory)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        replace_file(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
