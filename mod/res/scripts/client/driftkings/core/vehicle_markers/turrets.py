# -*- coding: utf-8 -*-
"""Describe a visible vehicle's stock turret without guessing missing gun prices."""


def classify(descriptor, price):
    result = {'stock-turret': None, 'turret-vulnerability': None}
    vehicle = getattr(descriptor, 'type', None)
    rows = getattr(vehicle, 'turrets', ())
    current = getattr(descriptor, 'turret', None)
    if not rows or not rows[0] or current is None:
        return result
    row = rows[0]
    ids = [getattr(turret, 'compactDescr', None) for turret in row]
    actual = getattr(current, 'compactDescr', None)
    if actual is None or actual not in ids:
        return result
    stock = len(row) > 1 and actual != ids[-1]
    result['stock-turret'] = stock
    if not stock or row[0].maxHealth == row[-1].maxHealth:
        result['turret-vulnerability'] = 'none'
    elif not getattr(row[-1], 'unlocks', ()):
        result['turret-vulnerability'] = 'low'
    else:
        prices = [[price(vehicle, gun) for gun in turret.guns] for turret in (row[0], row[-1])]
        result['turret-vulnerability'] = 'unknown'
        if all(values and all(value is not None for value in values) for values in prices):
            result['turret-vulnerability'] = 'low' if max(prices[0]) >= max(prices[1]) else 'high'
    return result


_prices = {}


def gun_price(vehicle, gun):
    import nations
    import ResMgr
    nation = nations.NAMES[vehicle.id[0]]
    key = (nation, gun.name)
    if key not in _prices:
        section = ResMgr.openSection('scripts/item_defs/vehicles/' + nation + '/components/guns.xml/shared/' + gun.name)
        _prices[key] = section.readInt('price') if section is not None and section.has_key('price') else None
    return _prices[key]
