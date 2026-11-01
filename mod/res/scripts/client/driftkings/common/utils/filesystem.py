# -*- coding: utf-8 -*-
"""Small file helpers compatible with the client's Python 2 runtime."""
import hashlib
import os
import tempfile


def recover_file(target):
    # Preserve pre-rename JSON settings on case-sensitive filesystems. Windows
    # already opens the old spelling; never replace a user's existing document.
    directory, name = os.path.split(target)
    if (not os.path.exists(target) and name == name.lower() and name.endswith('.json')
            and os.path.isdir(directory)):
        candidates = [item for item in os.listdir(directory) if item.lower() == name]
        if len(candidates) > 1:
            raise ValueError('Ambiguous settings filename: ' + target)
        if candidates and os.path.isfile(os.path.join(directory, candidates[0])):
            os.rename(os.path.join(directory, candidates[0]), target)
    previous = target + '.previous'
    if not os.path.exists(target) and os.path.isfile(previous):
        os.rename(previous, target)


def replace_file(source, target):
    replace = getattr(os, 'replace', None)
    if callable(replace):
        replace(source, target)
        return
    if os.name != 'nt':
        os.rename(source, target)
        return
    # The game's Python 2.7 does not include the native _ctypes module.
    # Preserve the old document until the new one has been published.
    recover_file(target)
    previous = target + '.previous'
    if os.path.exists(previous):
        os.remove(previous)
    had_target = os.path.isfile(target)
    if had_target:
        os.rename(target, previous)
    try:
        os.rename(source, target)
    except Exception:
        if had_target:
            os.rename(previous, target)
        raise
    if had_target:
        os.remove(previous)


def file_sha256(path):
    """Hash a file in bounded chunks; propagate read failures to its caller."""
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def atomicWrite(path, data):
    """Replace a file only after its complete replacement has been written."""
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
