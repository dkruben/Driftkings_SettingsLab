# -*- coding: utf-8 -*-
"""Public battle identity and current entity positions; never use hidden/last-known positions."""

from driftkings.core.vehicle_markers.turrets import classify, gun_price


def context(player, entity, vehicle_id, vehicle, include_distance=False):
    own_id = getattr(player, 'playerVehicleID', 0)
    arena = getattr(player, 'arena', None)
    own = getattr(arena, 'vehicles', {}).get(own_id, {})
    team = getattr(player, 'team', None)
    platoon = vehicle.get('prebattleID')
    result = {'player': vehicle_id == own_id, 'ally': vehicle.get('team') == team,
              'enemy': vehicle.get('team') != team,
              'squad': bool(vehicle.get('team') == team and platoon and platoon == own.get('prebattleID')),
              'anonym': bool(vehicle.get('isAnonymized')), 'distance': None, 'dist': None}
    target = entity(vehicle_id)
    result.update(classify(getattr(target, 'typeDescriptor', None), gun_price))
    if include_distance:
        attached = player.getVehicleAttached()
        origin = player.getOwnVehiclePosition() if attached is not None and attached.isAlive() else getattr(player, 'position', None)
        position = getattr(target, 'position', None)
        if position is not None and origin is not None:
            distance = (position - origin).length
            if distance >= 0:
                result['distance'] = result['dist'] = int(distance + .5)
    return result
