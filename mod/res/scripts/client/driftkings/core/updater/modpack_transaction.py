# -*- coding: utf-8 -*-
"""Prepare bounded native tickets and verify complete post-install receipts."""
import json
import os

from driftkings.core.updater.inventory import file_signature, Inventory, require
from driftkings.core.updater.manifest import bounded_json, MAX_MANIFEST
from driftkings.core.updater.versioning import Version

RECEIPT = 'ownership.%s.json'
FIELDS = set(('schema', 'gameVersion', 'version', 'size', 'sha256', 'installedVersion',
              'installedSize', 'installedSha256', 'inventory', 'operations', 'previousReceipt', 'owned'))


def ownership(raw, game_version, installed):
    if raw is None:
        return None, ()
    value = bounded_json(raw)
    require(isinstance(value, dict) and set(value) == set(('schema', 'inventory', 'owned')) and
            type(value['schema']) is int and value['schema'] == 1, 'Invalid ownership receipt')
    document = value['inventory']
    require(isinstance(document, dict), 'Invalid ownership inventory')
    version = Version(document.get('version'))
    channel = 'beta' if version.prerelease else 'stable'
    inventory = Inventory(document, version.text, channel, game_version)
    paths = set(item['path'] for item in inventory.files if item['kind'] in ('code', 'dependency'))
    require(isinstance(value['owned'], list) and len(value['owned']) == len(set(value['owned'])) and
            set(value['owned']).issubset(paths), 'Invalid owned paths')
    if version.text != installed:
        # A manual upgrade/downgrade invalidates ownership, not personal files.
        # Keep the raw receipt for rollback, but migrate code by its identity
        # and treat all existing dependencies as shared.
        return None, ()
    return inventory, tuple(value['owned'])


def planned(inventory, observed, previous, owned):
    operations = inventory.plan(observed, previous, owned)
    for item in operations:
        require(item['action'] != 'conflict', 'Shared dependency or owned code changed: ' + item['path'])
        if item['action'] == 'verify_legacy_code':
            item['action'] = 'replace'
    # Commit the unified version after its dependencies, then the receipt.
    code = next(item['path'] for item in inventory.files if item['kind'] == 'code')
    operations.sort(key=lambda item: (item['path'] == code, item['path']))
    next_owned = sorted(item['path'] for item in operations if item['after'] is not None and
                        (item['action'] in ('install', 'replace') or item['path'] in owned))
    return operations, next_owned


def prepare(root, manifest, installed, installed_size, installed_sha256):
    from driftkings.core.updater.installer import safe_file
    from driftkings.core.updater.results import safe_path
    inventory = manifest.inventory
    receipt = os.path.join(root, 'mods', 'configs', 'driftkings', 'cache', 'update', RECEIPT % inventory.game_version)
    safe_path(receipt)
    raw = None
    if os.path.lexists(receipt):
        with open(safe_file(receipt), 'rb') as stream:
            raw = stream.read(MAX_MANIFEST + 1)
        bounded_json(raw)
        raw = raw.decode('utf-8')
    previous, owned = ownership(raw, inventory.game_version, installed)
    paths = set(item['path'] for item in inventory.files if item['kind'] in ('code', 'dependency')) | set(owned)
    observed = {}
    for path in paths:
        target = safe_path(os.path.join(root, *path.split('/')))
        observed[path] = file_signature(safe_file(target)) if os.path.lexists(target) else None
    operations, next_owned = planned(inventory, observed, previous, owned)
    ticket = dict(schema=2, gameVersion=inventory.game_version, version=manifest.version.text,
                  size=manifest.payload_size, sha256=manifest.payload_sha256, installedVersion=installed,
                  installedSize=installed_size, installedSha256=installed_sha256, inventory=inventory.document(),
                  operations=operations, previousReceipt=raw, owned=next_owned)
    validate_ticket(ticket, manifest)
    # Use the native reader's same bounded size before writing any ticket.
    bounded_json(json.dumps(ticket, ensure_ascii=False))
    return ticket


def validate_ticket(ticket, manifest):
    require(isinstance(ticket, dict) and set(ticket) == FIELDS and type(ticket['schema']) is int and ticket['schema'] == 2,
            'Invalid modpack ticket fields')
    require(manifest.inventory is not None and ticket['inventory'] == manifest.inventory.document() and
            ticket['gameVersion'] == manifest.game_version and ticket['version'] == manifest.version.text and
            ticket['size'] == manifest.payload_size and ticket['sha256'] == manifest.payload_sha256 and
            Version(ticket['installedVersion']) < manifest.version, 'Modpack ticket identity mismatch')
    previous, owned = ownership(ticket['previousReceipt'], ticket['gameVersion'], ticket['installedVersion'])
    require(isinstance(ticket['operations'], list) and len(ticket['operations']) <= 512, 'Invalid operations')
    observed = {}
    for item in ticket['operations']:
        require(isinstance(item, dict) and set(item) == set(('path', 'action', 'before', 'after')) and
                item['path'] not in observed, 'Invalid or duplicate operation')
        observed[item['path']] = item['before']
    operations, next_owned = planned(manifest.inventory, observed, previous, owned)
    require(ticket['operations'] == operations and ticket['owned'] == next_owned, 'Modpack plan changed')
    code = next(item for item in operations if item['path'].endswith('/driftkings.wotmod'))
    require(code['before'] == dict(size=ticket['installedSize'], sha256=ticket['installedSha256']), 'Installed package observation mismatch')
    return ticket


def verify_result(root, ticket, loaded_version, old=False):
    from driftkings.core.updater.downloader import validate_package
    from driftkings.core.updater.results import safe_path
    version = ticket['installedVersion'] if old else ticket['version']
    require(loaded_version == version, 'Loaded version differs from transaction')
    for item in ticket['operations']:
        if item['action'] == 'keep_unowned':
            continue
        expected = item['before'] if old else item['after']
        target = safe_path(os.path.join(root, *item['path'].split('/')))
        if expected is None:
            require(not os.path.lexists(target), 'Removed/rolled-back file still exists')
        else:
            require(os.path.isfile(target) and file_signature(target) == expected, 'Installed modpack file differs')
        if item['path'].endswith('/driftkings.wotmod'):
            validate_package(target, version)
    receipt = safe_path(os.path.join(root, 'mods', 'configs', 'driftkings', 'cache', 'update', RECEIPT % ticket['gameVersion']))
    if old:
        if ticket['previousReceipt'] is None:
            require(not os.path.lexists(receipt), 'Unexpected ownership receipt after rollback')
        else:
            with open(receipt, 'rb') as stream:
                require(stream.read(MAX_MANIFEST + 1).decode('utf-8') == ticket['previousReceipt'], 'Old ownership receipt changed')
    else:
        with open(receipt, 'rb') as stream:
            value = bounded_json(stream.read(MAX_MANIFEST + 1))
        require(value == dict(schema=1, inventory=ticket['inventory'], owned=ticket['owned']), 'Installed ownership receipt differs')
