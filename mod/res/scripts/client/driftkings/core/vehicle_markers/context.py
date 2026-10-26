# -*- coding: utf-8 -*-
"""Public battle identity and current entity positions; never use hidden/last-known positions."""
from driftkings.core.vehicle_markers.turrets import classify, gun_price

# XVM keeps each vehicle's place in its team list from the first roster; deaths do not reorder it.
_positions = {'arena': None, 'values': {}}


def team_order(arena, team):
    """Vehicle ids of one team in the client's player-panel order (WG sort key)."""
    try:
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        from gui.battle_control.arena_info import vos_collections
        provider = dependency.instance(IBattleSessionProvider).getArenaDP()
        collection = vos_collections.AllyItemsCollection() if provider.isAllyTeam(team) else vos_collections.EnemyItemsCollection()
        return list(collection.ids(provider))
    except Exception:
        return sorted(ident for ident, vehicle in arena.vehicles.items() if vehicle.get('team') == team)


def position(arena, vehicle_id, vehicle):
    # A battle is identified by its unique id; no reference to the arena is kept.
    owner = (id(arena), getattr(arena, 'arenaUniqueID', None))
    if _positions['arena'] != owner:
        _positions['arena'] = owner
        _positions['values'] = {}
    values = _positions['values']
    if vehicle_id not in values:
        for index, ident in enumerate(team_order(arena, vehicle.get('team')), 1):
            values.setdefault(ident, index)
    return values.get(vehicle_id)


def battle_type(arena):
    """XVM's {{battletype}}: empty in regular random battles, otherwise the bonus type name."""
    bonus = getattr(arena, 'bonusType', None)
    if bonus in (None, 1):
        return ''
    try:
        from constants import ARENA_BONUS_TYPE_NAMES
    except ImportError:
        return str(bonus)
    # The client table maps names to numbers.
    names = dict((number, name) for name, number in ARENA_BONUS_TYPE_NAMES.items())
    return str(names.get(bonus, bonus)).lower()


def context(player, entity, vehicle_id, vehicle, include_distance=False):
    own_id = getattr(player, 'playerVehicleID', 0)
    arena = getattr(player, 'arena', None)
    own = getattr(arena, 'vehicles', {}).get(own_id, {})
    team = getattr(player, 'team', None)
    platoon = vehicle.get('prebattleID')
    result = {'player': vehicle_id == own_id, 'ally': vehicle.get('team') == team,
              'enemy': vehicle.get('team') != team,
              'squad': bool(vehicle.get('team') == team and platoon and platoon == own.get('prebattleID')),
              'anonym': bool(vehicle.get('isAnonymized')), 'distance': None, 'dist': None,
              'battletype': battle_type(arena), 'position': position(arena, vehicle_id, vehicle) if arena is not None else None}
    target = entity(vehicle_id)
    result.update(classify(getattr(target, 'typeDescriptor', None), gun_price))
    if include_distance:
        attached = player.getVehicleAttached()
        origin = player.getOwnVehiclePosition() if attached is not None and attached.isAlive() else getattr(player, 'position', None)
        target_position = getattr(target, 'position', None)
        if target_position is not None and origin is not None:
            distance = (target_position - origin).length
            if distance >= 0:
                result['distance'] = result['dist'] = int(distance + .5)
    return result
