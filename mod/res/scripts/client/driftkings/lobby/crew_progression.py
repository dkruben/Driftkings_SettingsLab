# -*- coding: utf-8 -*-
"""Read current native crew costs without modifying inventory or training."""
from driftkings.core.crew_progression import progression
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.CrewProgression')


def collect_tankman(tankman, items, slot=None):
    row = {'slot': slot, 'id': None, 'name': '', 'role': '',
           'state': 'empty', 'remainingXP': None, 'estimatedBattles': None,
           'averageXP': None, 'roleTraining': False}
    if tankman is None:
        return row
    row['state'] = 'unavailable'
    try:
        row.update(id=tankman.invID, name=tankman.getFullUserNameWithSkin(),
                   role=tankman.roleUserName)
        complete = tankman.allSkillsLearned()
        # Native API sums only the unfinished skill to 100%, including free XP.
        # getNextLevelXpCost would instead stop at the next percentage point.
        remaining = 0 if complete else tankman.getNextSkillXpCost()
        # Native free XP can exceed the remaining skill cost.
        if remaining is not None and remaining < 0:
            remaining = 0
        average = None
        # Unassigned crew dossiers use account statistics, not personal history.
        if remaining is not None and remaining > 0 and tankman.isInTank:
            dossier = items.getTankmanDossier(tankman.invID)
            average = dossier.getAvgXP() if dossier is not None and dossier.getBattlesCount() else None
        row.update(progression(remaining, average, complete))
        row['roleTraining'] = not tankman.isMaxRoleLevel
    except Exception:
        LOG.exception('Could not read crew progression for slot %s', slot)
        row.update(state='unavailable')
    return row


def collect_rows(vehicle, items):
    return [collect_tankman(tankman, items, slot) for slot, tankman in vehicle.crew] if vehicle is not None else []
