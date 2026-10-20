# -*- coding: utf-8 -*-
"""Bounded, atomic JSON download to a local cache file. Python 2.7/3; no game-engine imports.

The cache file is only replaced by a complete, valid JSON document, so an interrupted or failed
download can never leave a truncated or placeholder file behind. Run it off the client thread.
"""
import json
import logging
import os

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

LOG = logging.getLogger('Driftkings.Download')
MAX_BYTES = 8 * 1024 * 1024


def download_json(url, path, timeout=10, limit=MAX_BYTES, opener=urlopen):
    """True when path now holds the freshly downloaded document; False (cache untouched) otherwise."""
    temporary = path + '.tmp'
    try:
        response = opener(url, timeout=timeout)
        try:
            status = response.getcode() if hasattr(response, 'getcode') else 200
            if status != 200:
                raise ValueError('HTTP %s' % status)
            data = response.read(limit + 1)
        finally:
            response.close()
        if not data or len(data) > limit:
            raise ValueError('Empty or oversized response')
        json.loads(data.decode('utf-8'))
        with open(temporary, 'wb') as stream:
            stream.write(data)
        if os.name == 'nt' and os.path.exists(path):
            os.remove(path)  # Python 2 on Windows cannot rename over an existing file
        os.rename(temporary, path)
        return True
    except Exception as error:
        LOG.warning('Could not refresh %s: %s', url, error)
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except OSError:
            pass
        return False
